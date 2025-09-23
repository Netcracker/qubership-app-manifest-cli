import sys, typer, json
from typing import Optional
from ..services.components import add_component as _add_component
from ..services.dependencies import add_dependency as _add_dependency

def add_command(
    manifest: str = typer.Argument(...),
    section: str = typer.Argument(...),
    text: Optional[str] = typer.Option(None, "--text"),
    file: Optional[typer.FileText] = typer.Option(None, "--file", "-f"),
    configuration: Optional[str] = typer.Option(None, "--config", "-c"),
    out: Optional[typer.FileTextWrite] = typer.Option(None, "--out", "-o"),
):
    payload_text = file.read() if file else (text if text is not None else sys.stdin.read())
    if section == "components":
        _add_component(manifest, payload_text, out)
    elif section == "dependencies":
        _add_dependency(manifest, payload_text, configuration, out)
    else:
        raise typer.BadParameter("section must be 'components' or 'dependencies'")
