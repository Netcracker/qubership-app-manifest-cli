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
SUPPORTED_URL_PURL_TYPES = ["docker", "helm", "github"]
MIME_TO_PURL_TYPE = {
    "application/vnd.docker.image": "docker",
    "application/vnd.qubership.helm.chart": "helm",
}


def purl_2_url(purl: str, reg_config: str="") -> str:
    """
    Converts a Package URL (purl) to a standard URL.
    For example, converts 'pkg:helm/bitnami/nginx?version=1.2.3' to 'https://charts.bitnami.com/bitnami/nginx-1.2.3.tgz'
    """
    return purl
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
            if qual.startswith('registry_name='):
                registry_id = qual.split('=')[1]
                break
    if registry_id == '':
        raise ValueError("Docker purl must have registry_name qualifier")
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
    # Затычка
    """
    Converts a Helm Package URL (purl) to a standard URL.
    For example, converts 'pkg:helm/bitnami/nginx?version=1.2.3' to 'https://charts.bitnami.com/bitnami/nginx-1.2.3.tgz'
    """
    return "https://example.com/chart.tgz"

def github_purl_2_url(purl: str, reg_config: str) -> str:
    # Затычка
    return "https://github.com/owner/repo/repo.tar.gz"

# url_2_purl
# Входные параметры:
# url - строка с URL
# type - строка с типом (docker, helm, github) или mime-type (application/vnd.docker.image, application/vnd.qubership.helm.chart)
# Выходные данные:
# возвращает строку с purl
def url_2_purl(url: str, type: str) -> str:
    print(f"  Generating purl from url: {url} with type: {type}")
    purl = ""
    if type not in SUPPORTED_URL_PURL_TYPES and not type.startswith("application/"):
        raise ValueError(f"Unsupported type: {type}. Supported types are: {SUPPORTED_URL_PURL_TYPES} or mime-types")
    if type.startswith("application/"): # Если в качестве типа передан mime-type, то конвертирую его в purl type
        if type not in MIME_TO_PURL_TYPE:
            return ""
        purl_type = MIME_TO_PURL_TYPE[type]
        if url.startswith('https://github.com'):
            purl_type = "github"
    else:
        purl_type = type
    # Проверяю, что url содержит github.com, если тип github
    if purl_type == "github" and "github.com" not in url:
        raise ValueError("GitHub purl can only be generated from github.com URLs")
    print(f"    Detected purl type: {purl_type}")
    # Если тип docker
    if purl_type == "docker":
        # ghcr.io/owner/image:tag для GitHub Container Registry
        url_domain, url_body = url.split("/",1) # url_domain=ghcr.io, url_body=owner/image:tag

        if ':' in url_body:
            url_body, version = url_body.split(':', 1) # url_body=owner/image, version=tag
        else:
            version = "latest"
        if '/' not in url_body:
            raise ValueError("Invalid Container Registry URL")
        namespace, name = url_body.split('/', 1) # namespace = owner, name = image
        purl = f"pkg:docker/{namespace}/{name}@{version}?registry_name={get_registry_by_param('groupUri', url_domain, 'dockerConfig')}"
    if purl_type == "helm":
        # oci://qubership-host/netcracker/qubership-core:2.1.0
        if url.startswith("oci://"):
            url_body = url[len("oci://"):] # qubership-host/netcracker/qubership-core:2.1.0
            url_domain, url_body = url_body.split("/",1) # url_domain=qubership-host, url_body=netcracker/qubership-core:2.1.0
            url_domain = "oci://" + url_domain
            if ':' in url_body:
                url_body, version = url_body.split(':', 1) # url_body=netcracker/qubership-core, version=2.1.0
            else:
                version = "latest"
            if '/' not in url_body:
                raise ValueError("Invalid OCI Helm Chart URL")
            namespace, name = url_body.split('/', 1) # namespace = netcracker, name = qubership-core
            purl = f"pkg:helm/{namespace}/{name}?version={version}&registry_name={get_registry_by_param('repositoryDomainName', url_domain, 'helmAppConfig')}"
    if purl_type == "github":
        # https://github.com/Netcracker/qubership-airflow/releases/download/2.0.1/airflow-1.19.0-dev.tgz
        if "github.com" not in url or "/releases/download/" not in url:
            raise ValueError("Invalid GitHub URL")
        url_domain = "https://github.com"
        url_body = url.split("github.com/",1)[1] # Netcracker/qubership-airflow/releases/download/2.0.1/airflow-1.19.0-dev.tgz
        namespace, version_and_file_name = url_body.split("/releases/download/",1) # namespace=Netcracker/qubership-airflow, version_and_file_name=2.0.1/airflow-1.19.0-dev.tgz
        version, file_name = version_and_file_name.split("/",1) # version=2.0.1, file_name=airflow-1.19.0-dev.tgz
        purl = f"pkg:github/{namespace}@{version}?file_name={file_name}&registry_name={get_registry_by_param('repositoryDomainName', url_domain, 'githubReleaseConfig')}"
    print(f"    Generated purl: {purl}")
    return purl

# get_registry_by_param:
# Входные параметры:
# regiestry_files_dir - директория с файлами реестров
# param_name - имя параметра, по которому ищем (например, groupUri для docker, repositoryDomainName для helmAppConfig и githubReleaseConfig)
# param_value - значение параметра, по которому ищем
# reg_type - тип реестра (dockerConfig, helmAppConfig, githubReleaseConfig)
# Выходные данные:
# возвращает name registry, если найден, иначе выбрасывает ValueError
def get_registry_by_param(param_name: str, param_value: str, reg_type: str, registry_files_dir: str = "configuration/RegDefs") -> str:
    import os
    import yaml
    if not os.path.isdir(registry_files_dir):
        raise ValueError(f"Registry files directory {registry_files_dir} does not exist or is not a directory")
    if reg_type not in ['dockerConfig', 'helmAppConfig', 'githubReleaseConfig']:
        raise ValueError(f"Unsupported registry type: {reg_type}. Supported types are: dockerConfig, helmAppConfig, githubReleaseConfig")
    reg_files = [os.path.join(registry_files_dir, f) for f in os.listdir(registry_files_dir) if os.path.isfile(os.path.join(registry_files_dir, f)) and f.endswith(('.yaml', '.yml'))]
    for reg_file in reg_files:
        with open(reg_file, "r") as f:
            reg_data = yaml.safe_load(f)
        if f'{reg_type}' not in reg_data:
            continue
        reg_config_data = reg_data[f'{reg_type}']
        if param_name in reg_config_data and reg_config_data[param_name] == param_value:
            return reg_data['name']
        else:
            continue
    raise ValueError(f"Registry with {param_name}={param_value} not found in {registry_files_dir}")

def get_version_from_purl(purl: str) -> str:
    if '@' not in purl:
        return "latest"
    purl_body = purl.split('@', 1)[1]
    if '?' in purl_body:
        version = purl_body.split('?', 1)[0]
    else:
        version = purl_body
    return version
