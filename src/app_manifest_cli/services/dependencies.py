import json


def add_dependency(manifest_path: str, payload_text: str, configuration: str, out_file):

    # Тут можно написать логику для депенденси

    item = json.loads(payload_text)
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    m.setdefault("dependencies", []).append(item)

    data = json.dumps(m, ensure_ascii=False, indent=2)
    if out_file:
        out_file.write(data)
    else:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(data)
