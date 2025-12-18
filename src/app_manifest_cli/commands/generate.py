import json, yaml, typer, os
from ..commands.create import create_command
from ..commands.create import get_bom_ref
from ..services.components import add_component as _add_component
from ..services.dependencies import add_dependency as _add_dependency
from ..services.purl_url import url_2_purl, get_version_from_purl
#from ..services.resource_profile_baseline import discover_standalone_runnable_component
from ..services.helm_discovery import helm_discovery
from pathlib import Path
from typing import List
from typing import Optional

def generate_command(
    components_files: List[Path] = typer.Argument(None, min=0, help="One or more file paths to process"),
    configuration: Optional[str] = typer.Option(None, "--config", "-c"),
    name: str = typer.Option(None, "--name", "-n", help="Application name"),
    version: str = typer.Option(None, "--version", "-v", help="Application version"),
    out: Optional[str] = typer.Option(None, "--out", "-o", help="Output file (default: stdout)"),
) -> None:
    try:
        if configuration is None:
            raise ValueError("Configuration file must be provided with --config option")
        configuration_data = load_configuration(configuration)
        if version == None and "applicationVersion" in configuration_data:
            version = configuration_data["applicationVersion"]
        if name == None and "applicationName" in configuration_data:
            name = configuration_data["applicationName"]
        if out == None:
            out = name + '-' + version + '.json'
        body = create_command(name=name, version=version, out=open(out, "w"))
        # Get components from config -- they define the manifest composition
        config_components = get_components_from_data(configuration_data)
        # Get dependencies from config
        config_dependencies = load_dependencies(config_components)
        # Read all JSON files with components
        json_components = []
        if components_files:
            for json_path in components_files:
                with open(json_path.resolve(), "r", encoding="utf-8") as f:
                    json_comp = json.load(f)
                    json_components.append(json_comp)
        # Iterate through components from config, if the same exists in json_components, then update it
        components = []
        for conf_comp in config_components:
            conf_comp['mime-type'] = conf_comp["mimeType"]
            for json_comp in json_components:
                if conf_comp["name"] == json_comp["name"] and conf_comp["mime-type"] == json_comp["mime-type"]:
                    typer.echo(f"Found update for component {conf_comp['name']}")
                    conf_comp.update(json_comp)
                    typer.echo(f"Updated component: {conf_comp}")
            if "bom-ref" not in conf_comp:
                conf_comp["bom-ref"] = get_bom_ref(conf_comp["name"])
            components.append(conf_comp)

        # Generate additional metadata for helm chart
        #   add properties named qubership:helm.values.artifactMappings
        #   with value as a dict, where key is bom-ref of dependency, and value is a dict with valuesPathPrefix key and value from configuration

        components = generate_helm_values_artifact_mappings(components)
        # If discovery is enabled, run it
        # enriching components with dependencies and properties
        # if discovery:
        components = helm_discovery(components)
        # Add all components to the manifest
        for comp in components:
            if comp.get("mime-type") == "application/vnd.qubership.standalone-runnable":
                if comp.get("version", "") == "":
                    comp["version"] = version
            typer.echo(f"Adding component: {comp['name']} with mime-type: {comp['mime-type']}")
            #typer.echo(f"comp details: {json.dumps(comp, indent=2)}")
            _add_component(manifest_path=out, payload_text=json.dumps(obj=comp,sort_keys=True), out_file=None)
        # Form a simple list of components for easy search
        components_list = [ comp["mime-type"] + ":" + comp["name"] for comp in components]
        for dep in config_dependencies:
            dep_record = {}
            if "ref" not in dep:
                raise ValueError("Each dependency must have a 'ref' field")
            if "dependsOn" not in dep:
                raise ValueError("Each dependency must have a 'dependsOn' field")
            if dep["ref"] not in components_list:
                raise ValueError(f"Dependency ref '{dep['ref']}' not found in components")
            dep_record["ref"] = next(comp for comp in components if (comp["mime-type"] + ":" + comp["name"]) == dep["ref"])["bom-ref"]
            dep_record["dependsOn"] = []
            for d in dep["dependsOn"]:
                if d not in components_list:
                    raise ValueError(f"Dependency dependsOn '{d}' not found in components")
                depends_on_component = next(comp for comp in components if (comp["mime-type"] + ":" + comp["name"]) == d)
                dep_record["dependsOn"].append(depends_on_component["bom-ref"])
            _add_dependency(manifest_path=out, payload_text=json.dumps(dep_record), configuration=None, out_file=None)
        typer.echo(f"Manifest generated and saved to {out}")
        with open('am.env', 'a') as f:
            f.write(f'PATH_APP_MANIFEST={out}\n')
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

def load_configuration(configuration: str) -> dict:
    # bomFormat: CycloneDX
    # specVersion: "1.6"
    # metadata:
    #   component:
    #   type: application
    #   mime-type: application/vnd.qubership.application
    #   name: qubership-integration-platform
    #   version: "1.0.0"
    # tools:
    #   components:
    #   - type: application
    #     name: sbom-generator
    #     version: "2.3.1"

    with open(configuration, "r") as f:
        configuration_data = yaml.safe_load(f)
    if "components" not in configuration_data:
        raise ValueError("Configuration file must contain 'components' section")
    # if "dependencies" not in configuration_data:
    #     raise ValueError("Configuration file must contain 'dependencies' section")
    return configuration_data

# Here I assume that in the config dependencies are described inside each component
# in the form of dependsOn list, where each element contains name and mime-type
# Transform this into a list of dictionaries with keys name, ref and dependsOn
# ref is mime-type:name
# dependsOn is a list of dependency refs
def load_dependencies(config_data: dict) -> List:
    deps = []
    for comp in config_data:
        comp["mime-type"] = comp["mimeType"]
        if comp.get('dependsOn'):
            deps_elem_name = f"{comp['name']}"
            deps_elem_ref = f"{comp['mime-type']}:{comp['name']}"
            deps_elem_depends_on = []
            for dep in comp['dependsOn']:
                if 'name' not in dep:
                    raise ValueError("Each dependency must have a 'name' field")
                if 'mime-type' not in dep and 'mimeType' not in dep:
                    raise ValueError("Each dependency must have a 'mime-type' or 'mimeType' field")
                deps_elem_depends_on.append(f"{dep.get('mimeType',dep.get('mime-type'))}:{dep['name']}")
            deps.append({"name": deps_elem_name, "ref": deps_elem_ref, "dependsOn": deps_elem_depends_on})
    return deps

# Function that receives a list of components from the manifest (to find bom-ref by name)
# What it does:
# 1. if component mime-type == application/vnd.qubership.helm.chart
# 2. if the component has dependsOn, iterate through all dependencies and check if each dependency has valuesPathPrefix parameter
# 3. if yes, create a dict with keys:
# "name": "qubership:helm.values.artifactMappings" and
# "value": {"dependency bom-ref": {"valuesPathPrefix": "value from dependency"}, ...}
# 4. add this dict to component properties
# 5. return the updated list of components
def generate_helm_values_artifact_mappings(manifest_components: List[dict]) -> dict | None:
    components = []
    for component in manifest_components:
        if component.get("mime-type") != "application/vnd.qubership.helm.chart":
            components.append(component)
            continue
        if not component.get("dependsOn"):
            components.append(component)
            continue
        artifact_mappings = {}
        for dep in component["dependsOn"]:
            if "valuesPathPrefix" in dep:
                dep_name = dep.get("name")
                dep_mime = dep.get("mimeType", dep.get("mime-type"))
                # Search in manifest_components for a component with the same name and mime-type to get its bom-ref
                matching_comp = next((comp for comp in manifest_components if comp["name"] == dep_name and comp["mime-type"] == dep_mime), None)
                print(f"  Processing dependency: {dep_name}, found matching component: {matching_comp is not None}")
                if matching_comp and "bom-ref" in matching_comp:
                    artifact_mappings[matching_comp["bom-ref"]] = {"valuesPathPrefix": dep["valuesPathPrefix"]}
                else:
                    raise ValueError(f"Dependency '{dep_name}' with mime-type '{dep_mime}' not found in manifest components or missing bom-ref")
        if artifact_mappings:
            if "properties" not in component:
                component["properties"] = []
            component["properties"].append({"name": "qubership:helm.values.artifactMappings", "value": artifact_mappings})
        components.append(component)
    return components

def get_components_from_data(data: dict) -> List[dict]:
    if "components" not in data:
        return []
    # components = []
    # for comp in data["components"]:
    #     if "name" not in comp or ("mime-type" not in comp and "mimeType" not in comp):
    #         raise ValueError("Each component must have 'name' and 'mime-type/mimeType' fields")
    #     mime_type = comp.get("mimeType",comp.get("mime-type"))
    #     purl = url_2_purl(comp.get("reference"), mime_type)
    #     version = comp.get("version", get_version_from_purl(purl))
    #     components.append({
    #         "name": comp["name"],
    #         "mime-type": mime_type,
    #         "version": version,
    #         "properties": comp.get("properties", []),
    #         "purl": purl,
    #         "reference": comp.get("reference"),
    #         "dependsOn": comp.get("dependsOn", [])
    #     })
    return data["components"]
