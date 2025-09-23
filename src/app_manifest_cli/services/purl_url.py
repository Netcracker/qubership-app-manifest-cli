def purl_2_url(purl: str) -> str:
    """
    Converts a Package URL (purl) to a standard URL.
    For example, converts 'pkg:helm/bitnami/nginx?version=1.2.3' to 'https://charts.bitnami.com/bitnami/nginx-1.2.3.tgz'
    """
    if not purl.startswith("pkg:helm/"):
        raise ValueError("Only helm purls are supported")
    # Remove 'pkg:helm/' prefix
    purl_body = purl[len("pkg:helm/"):]
    # Split by '?', to separate version if present
    if '?' in purl_body:
        name_part, query_part = purl_body.split('?', 1)
        query_params = dict(param.split('=') for param in query_part.split('&'))
        version = query_params.get('version', '')
    else:
        name_part = purl_body
        version = ''
    # Split name_part by '/', to get repo and chart name
    parts = name_part.split('/')
    if len(parts) != 2:
        raise ValueError("Purl must be in the format 'pkg:helm/repo/chartname'")
    repo, chart_name = parts
    # Construct URL
    base_url = f"https://charts.{repo}.com/{repo}"
    if version:
        url = f"{base_url}/{chart_name}-{version}.tgz"
    else:
        url = f"{base_url}/{chart_name}.tgz"
    return url

def url_2_purl(url: str) -> str:
    """
    Converts a standard URL to a Package URL (purl).
    For example, converts 'https://charts.bitnami.com/bitnami/nginx-1.2.3.tgz' to 'pkg:helm/bitnami/nginx?version=1.2.3'
    """
    if not url.startswith("https://charts."):
        raise ValueError("Only helm chart URLs are supported")
    # Remove 'https://charts.' prefix
    url_body = url[len("https://charts."):]
    # Split by '/', to separate repo and chart
    parts = url_body.split('/')
    if len(parts) < 2:
        raise ValueError("URL must be in the format 'https://charts.repo.com/repo/chartname-version.tgz'")
    repo = parts[0].split('.')[0]  # Extract repo from domain
    chart_part = parts[-1]  # Last part is chartname-version.tgz
    if not chart_part.endswith('.tgz'):
        raise ValueError("Chart URL must end with .tgz")
    chart_name_version = chart_part[:-len('.tgz')]  # Remove .tgz suffix
    # Split chart_name_version by last '-', to separate name and version
    if '-' in chart_name_version:
        last_dash_index = chart_name_version.rfind('-')
        chart_name = chart_name_version[:last_dash_index]
        version = chart_name_version[last_dash_index + 1:]
    else:
        chart_name = chart_name_version
        version = ''
    # Construct purl
    purl = f"pkg:helm/{repo}/{chart_name}"
    if version:
        purl += f"?version={version}"
    return purl
