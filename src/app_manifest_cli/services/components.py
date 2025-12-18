import json
from ..handlers.registry import get_handler
from ..commands.create import get_bom_ref

def add_component(manifest_path: str, payload_text: str, out_file):

   # Here you can add logic for adding a component to the manifest

    obj = json.loads(payload_text)
    if not obj.get("name"):
        raise ValueError("Component must have a 'name' field")
    if not obj.get("mime-type") and not obj.get("mime_type"):
        raise ValueError("Component must have a 'mime-type' field")
    if not obj.get("bom-ref"):
        obj["bom-ref"] = get_bom_ref(obj["name"])
    mime = obj.get("mime-type") or obj.get("mime_type")
    handler = get_handler(mime)
    item = handler(obj)

    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)

    m.setdefault("components", []).append(item["data"])
    data = json.dumps(m, ensure_ascii=False, indent=2)

    if out_file:
        out_file.write(data)
    else:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(data)
