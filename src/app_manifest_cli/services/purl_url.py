# pkg:[TYPE]/[NAMESPACE]/[NAME]@[VERSION]?[QUALIFIERS]#[SUBPATH]
#
# `pkg:` - обязательный префикс, указывающий что это Package URL
# `TYPE`- тип пакета/артефакта (docker, helm, github)
# `NAMESPACE` - группа/организация
# `NAME` - имя пакета/артефакта
# `@VERSION` - версия
# `?QUALIFIERS` - дополнительные параметры
# `#SUBPATH` - подпуть к файлу
import yaml
from typing import List

def purl_2_url(purl: str, reg_config: str) -> str:
    """
    Converts a Package URL (purl) to a standard URL.
    For example, converts 'pkg:helm/bitnami/nginx?version=1.2.3' to 'https://charts.bitnami.com/bitnami/nginx-1.2.3.tgz'
    """
    package_type = purl.split('/')[0].split(':')[1]
    if package_type not in ["helm", "docker", "github"]:
        raise ValueError(f"Unsupported package type: {package_type}")
    if package_type == "helm":
        return helm_purl_2_url(purl, reg_config)
    if package_type == "docker":
        return docker_purl_2_url(purl, reg_config)
    if package_type == "github":
        return github_purl_2_url(purl, reg_config)

def docker_purl_2_url(purl: str, reg_config: str) -> str:
    """
    Converts a Docker Package URL (purl) to a standard URL.
    For example, converts 'pkg:docker/library/nginx@1.19.0'
    to 'https://hub.docker.com/v2/repositories/library/nginx/tags/1.19.0'
    """

    # Remove 'pkg:docker/' prefix
    purl_body = purl[len("pkg:docker/"):]

    # Split by '#' to get subpath if present
    if '#' in purl_body:
        purl_body, subpath = purl_body.split('#', 1)
    else:
        subpath = None
    # Split by '?' to get qualifiers if present
    if '?' in purl_body:
        purl_body, qualifiers = purl_body.split('?', 1)
    else:
        qualifiers = None
    # Split by '@' to get version if present
    if '@' in purl_body:
        purl_body, version = purl_body.split('@', 1)
    else:
        version = 'latest'
    # Split by '/' to get name and namespace
    name, namespace = purl_body.split('/', 1)
    # Get the registry from qualifiers if present
    registry_id = ''
    if qualifiers:
        for qual in qualifiers.split('&'):
            if qual.startswith('registryName='):
                registry_id = qual.split('=')[1]
                break
    if registry_id == '':
        raise ValueError("Docker purl must have registryName qualifier")
    reg_config_data, reg_auth_data = get_registry(registry_id, reg_config, 'docker')

    # Construct URL
    return f"https://{reg_config_data['url']}/v2/repositories/{namespace}/{name}/tags/{version}"

def get_registry(registry_id: str, reg_config: str, reg_type: str) -> any:
    with open(reg_config, "r") as f:
        reg_data = yaml.safe_load(f)
    if f'{reg_type}Config' not in reg_data:
        raise ValueError(f"Registry {registry_id} must have {reg_type}Config section in registry config")
    reg_config_data = reg_data[f'{reg_type}Config']
    reg_auth_data = reg_data.get('authConfig', {}).get(reg_config_data.get('auth', ''), {})

    return reg_config_data, reg_auth_data

def helm_purl_2_url(purl: str, reg_config: str) -> str:
    """
    Converts a Helm Package URL (purl) to a standard URL.
    For example, converts 'pkg:helm/bitnami/nginx?version=1.2.3' to 'https://charts.bitnami.com/bitnami/nginx-1.2.3.tgz'
    """
    return "https://example.com/chart.tgz"

def github_purl_2_url(purl: str, reg_config: str) -> str:
    return "https://github.com/owner/repo/repo.tar.gz"
