from ..commands.create import get_bom_ref

def handle(obj: dict) -> dict:

    # DAO Here you can add logic for processing incoming json standalone-runnable
    STANDALONE_RUNNABLE_REQUIRED_FIELDS = [
        "type",
        "mime-type",
        "bom-ref",
        "name",
        "properties",
        "components"
    ]
    STANDALONE_RUNNABLE_FIELDS = STANDALONE_RUNNABLE_REQUIRED_FIELDS + ["version"]
    if "name" not in obj or obj.get("name", "") == "":
        raise ValueError("Missing required field 'name' in standalone-runnable component")
    if "type" not in obj or obj.get("type", "") == "":
        obj["type"] = "application"
    if "properties" not in obj:
        obj["properties"] = []
    if "components" not in obj:
        obj["components"] = []
    if "bom-ref" not in obj or obj.get("bom-ref", "") == "":
        obj["bom-ref"] = get_bom_ref(obj.get("name", ""))
    for field in list(obj.keys()):
        if field not in STANDALONE_RUNNABLE_FIELDS:
            print(f"  Warning: Unknown field '{field}' in standalone-runnable component")
            obj.pop(field)
    return {"strategy": "standalone_runnable", "data": obj}
