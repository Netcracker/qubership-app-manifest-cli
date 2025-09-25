import json, yaml, typer
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
    name: str = typer.Option(
        "qubership-integration-platform", "--name", help="Application name"
    ),
    version: str = typer.Option("", "--version", help="Application version"),
    out: Optional[str] = typer.Option(None, "--out", "-o", help="Output file (default: stdout)"),
    discovery: bool = typer.Option(False, "--discovery", help="Enable component discovery"),
) -> None:
    configuration_data = load_configuration(configuration)
    if version == "" and "version" in configuration_data.get("metadata", {}).get("component", {}):
        version = configuration_data["metadata"]["component"]["version"]
    body = create_command(name=name, version=version, out=open(out, "w"))
    # Получаю компоненты из конфига -- именно они определяют состав манифеста
    config_components = get_components_from_data(configuration_data)
    # Получаю депенденси из конфига
    config_dependencies = load_dependencies(config_components)
    # Читаю все json файлы с компонентами
    json_components = []
    if components_files:
        for json_path in components_files:
            with open(json_path.resolve(), "r", encoding="utf-8") as f:
                json_comp = json.load(f)
                json_components.append(json_comp)
    # Перебираю компоненты из конфига, если в json_components есть такой же, то обновляю его
    components = []
    for conf_comp in config_components:
        for json_comp in json_components:
            if conf_comp["name"] == json_comp["name"] and conf_comp["mime-type"] == json_comp["mime-type"]:
                conf_comp.update(json_comp)
        if "bom-ref" not in conf_comp:
            conf_comp["bom-ref"] = get_bom_ref(conf_comp["name"])
        components.append(conf_comp)

    # Генерирую дополнительные метаданные для helm chart
    #   добавляю properies с именем qubership:helm.values.artifactMappings
    #   и значением в виде dict, где ключ - bom-ref зависимости, а значение - dict с ключом valuesPathPrefix и значением из конфигурации

    components = generate_helm_values_artifact_mappings(components)
    # Если включено discovery, то запускаю его
    # дополняя компоненты зависимостями и свойствами
    if discovery:
        components = helm_discovery(components)
    # Добавляю все компоненты в манифест
    for comp in components:
        # Удаляю dependsOn, чтобы не было в манифесте
        comp.pop("dependsOn", None)
        comp.pop("reference", None)
        # if comp.get("mime-type") == "application/vnd.qubership.standalone-runnable":
        #     if resources_dir is None:
        #         raise ValueError("When component with mime-type 'application/vnd.qubership.standalone-runnable' provided in configuration, --resources-dir must be specified")
        #     comp = discover_standalone_runnable_component(comp, resources_dir)

        typer.echo(f"Adding component: {comp['name']} with mime-type: {comp['mime-type']}")
        #typer.echo(f"comp details: {json.dumps(comp, indent=2)}")
        _add_component(manifest_path=out, payload_text=json.dumps(comp), out_file=None)
    # Формирую простой список компонент для удобства поиска
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

# Здесь я предполагаю, что в конфиге dependencies описываются внутри каждого компонента
# в виде списка dependsOn, где каждый элемент содержит name и mime-type
# Преобразую это в список словарей с ключами name, ref и dependsOn
# ref - это mime-type:name
# dependsOn - это список ref зависимостей
def load_dependencies(config_data: dict) -> List:
    deps = []
    for comp in config_data:
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

# Функция, которая получает на вход список компонент из манифеста (чтобы найти bom-ref по имени)
# Что она делает:
# 1. если mime-type компоненты == application/vnd.qubership.helm.chart
# 2. если у компонента есть dependsOn, то перебирает все зависимости и проверяет есть ли у каждой зависимости параметр valuesPathPrefix
# 3. если есть, то создаёт dict с ключами:
# "name": "qubership:helm.values.artifactMappings" и
# "value": {"bom-ref зависимости": {"valuesPathPrefix": "значение из зависимости"}, ...}
# 4. добавляет этот dict в properties компонента
# 5. возвращает обновлённый список компонентов
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
                # Ищу в manifest_components компонент с таким же name и mime-type, чтобы взять его bom-ref
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
    components = []
    for comp in data["components"]:
        if "name" not in comp or ("mime-type" not in comp and "mimeType" not in comp):
            raise ValueError("Each component must have 'name' and 'mime-type/mimeType' fields")
        mime_type = comp.get("mimeType",comp.get("mime-type"))
        purl = url_2_purl(comp.get("reference"), mime_type)
        version = comp.get("version", get_version_from_purl(purl))
        components.append({
            "name": comp["name"],
            "mime-type": mime_type,
            "version": version,
            "properties": comp.get("properties", []),
            "purl": purl,
            "reference": comp.get("reference"),
            "dependsOn": comp.get("dependsOn", [])
        })
    return components
