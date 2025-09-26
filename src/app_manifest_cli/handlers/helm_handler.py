from ..services.purl_url import get_version_from_purl, url_2_purl
from ..commands.create import get_bom_ref

def handle(obj: dict) -> dict:

    # DAO Тут можно добавить логику обработки входящего json Helm Chart
    CHART_REQUIRED_FIELDS = [
        "type",
        "mime-type",
        "bom-ref",
        "name",
        "purl",
        "properties",
        "components"
    ]
    CHART_FIELDS = CHART_REQUIRED_FIELDS + ["version", "hashes"]
    if "purl" not in obj or obj.get("purl", "") == "":
        if "reference" in obj and obj.get("reference", "") != "":
            obj["purl"] = url_2_purl(obj["reference"], "helm")
        else:
            raise ValueError("Missing required field 'purl' in helm chart component")
    if "type" not in obj or obj.get("type", "") == "":
        obj["type"] = "application"
    if "version" not in obj or obj.get("version", get_version_from_purl(obj.get("purl"))) == "":
        obj["version"] = "latest"
    if "properties" not in obj:
        obj["properties"] = []
    if "components" not in obj:
        obj["components"] = []
    if "bom-ref" not in obj or obj.get("bom-ref", "") == "":
        obj["bom-ref"] = get_bom_ref(obj.get("name", ""))
    for field in CHART_REQUIRED_FIELDS:
        if field not in obj:
            raise ValueError(f"Missing required field '{field}' in helm chart component")
    for field in list(obj.keys()):
        if field not in CHART_FIELDS:
            print(f"  Warning: Unknown field '{field}' in helm chart component")
            obj.pop(field)
    #print("Running helm_chart handler")
    return {"strategy": "helm", "data": obj}
