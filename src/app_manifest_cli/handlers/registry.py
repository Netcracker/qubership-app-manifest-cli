from .default import handle as default_handle
from .docker_handler import handle as docker_handle
from .helm_handler import handle as helm_handle
from .standalone_runnable_handler import handle as standalone_runnable_handle

_HANDLERS = {
    "application/vnd.docker.image": docker_handle,
    "application/vnd.qubership.helm.chart": helm_handle,
    "application/vnd.qubership.standalone-runnable": standalone_runnable_handle,
}

def get_handler(mime: str):
    return _HANDLERS.get(mime, default_handle)
