from ..services.purl_url import get_group_from_purl, get_version_from_purl, url_2_purl
from ..commands.create import get_bom_ref

def handle(obj: dict) -> dict:

    # DAO Тут можно добавить логику обработки входящего json  Docker Image
    DOCKER_REQUIRED_FIELDS = ["type",
        "mime-type",
        "bom-ref",
        "group",
        "name",
        "version",
        "purl"]
    DOCKER_FIELDS = DOCKER_REQUIRED_FIELDS + ["hashes"]
    if "purl" not in obj or obj.get("purl", "") == "":
        if "reference" in obj and obj.get("reference", "") != "":
            obj["purl"] = url_2_purl(obj["reference"], "docker")
        else:
            raise ValueError("Missing required field 'purl' in docker image component")
    if "type" not in obj or obj.get("type", "") == "":
        obj["type"] = "container"
    if "group" not in obj or obj.get("group", "") == "":
        obj["group"] = get_group_from_purl(obj.get("purl", ""))
    if "version" not in obj or obj.get("version", "") == "":
        obj["version"] = get_version_from_purl(obj.get("purl", ""))
    if "bom-ref" not in obj or obj.get("bom-ref", "") == "":
        obj["bom-ref"] = get_bom_ref(obj.get("name", ""))
    if "hashes" in obj and obj["hashes"] != []:
        for hash in obj["hashes"]:
            hash['alg'] = format_hash_name(hash['alg'])

    for field in DOCKER_REQUIRED_FIELDS:
        if field not in obj:
            raise ValueError(f"Missing required field '{field}' in docker image component")
    #print("Running docker_image handler")
    # удаляю лишние поля из obj
    for field in list(obj.keys()):
        if field not in DOCKER_FIELDS:
            print(f"  Warning: Unknown field '{field}' in docker image component")
            obj.pop(field)
    return {"strategy": "docker", "data": obj}

def format_hash_name(hash_str):
    hash_algs = {
        "md5": "MD5",
        "sha256": "SHA-256",
        "sha384": "SHA-384",
        "sha512": "SHA-512"
    }
    return hash_algs.get(hash_str, hash_str.upper())
