import sys, typer, json, uuid, datetime
from importlib.metadata import version, PackageNotFoundError

app = typer.Typer()


def get_uuid() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def get_timestamp() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def get_bom_ref(name: str) -> str:
    return f"{name}:{uuid.uuid4()}"


try:
    app_version = version("app-manifest-cli")
except PackageNotFoundError:
    app_version = "0.0.0"


def create_command(
    name: str = typer.Option(
        "qubership-integration-platform", "--name", help="Application name"
    ),
    version: str = typer.Option("1.2.3", "--version", help="Application version"),
    out: typer.FileTextWrite = typer.Option(
        sys.stdout, "--out", "-o", help="Output file (default: stdout)"
    ),
):
    body = {
        "serialNumber": get_uuid(),
        "$schema": "../schemas/application-manifest.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "timestamp": get_timestamp(),
            "component": {
                "bom-ref": get_bom_ref(name),
                "type": "application",
                "mime-type": "application/vnd.qubership.application",
                "name": name,
                "version": version,
            },
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "sbom_generator",
                        "version": app_version,
                    }
                ]
            },
        },
        "components": [],
        "dependencies": [],
    }
    out.write(json.dumps(body, ensure_ascii=False, indent=2))
    return body
