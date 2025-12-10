# Здесь происходит наполнение данных о компоненте с mime-type application/vnd.qubership.standalone-runnable
# Входные данные:
# - путь к каталогу с файлами конфигурации (.yaml или .yml или .json)
# - dict компоненты, в которую нужно добавить вложенные объекты с конфигурациями
# Выходные данные: dict вида
    # {
    #   "bom-ref": "qubership-jaeger:61439aff-c00d-43f5-9bae-fe6db05db2d5",
    #   "type": "application",
    #   "mime-type": "application/vnd.qubership.standalone-runnable",
    #   "name": "qubership-jaeger",
    #   "version": "1.2.3",
    #   "properties": [],
    #   "components": [
    #     {
    #       "bom-ref": "resource-profile-baselines:61439a11-c00d-43f5-9bae-fe6db05db2d5",
    #       "type": "data",
    #       "mime-type": "application/vnd.qubership.resource-profile-baseline",
    #       "name": "resource-profile-baselines",
    #       "data": [
    #         {
    #           "type": "configuration",
    #           "name": "small.yaml",
    #           "contents": {
    #             "attachment": {
    #               "contentType": "application/yaml",
    #               "encoding": "base64",
    #               "content": "0YMg0LzQtdC90Y8g0L3QtSDQsdGL0LvQviDQv9GA0LjQvNC10YDQsCwg0L/QvtGN0YLQvtC80YMg0YLRg9GCINGN0YLQvtGCINGC0LXQutGB0YIuCtGC0YPRgiDQtNC+0LvQttC10L0g0LHRi9GC0Ywg0L/Qu9C+0YHQutC40Lkg0LTQttGB0L7QvSDQuNC3IH4gMTAg0LrQuC/QstGN0LvRjNGO"
    #             }
    #           }
    #         },
    #         {
    #           "type": "configuration",
    #           "name": "medium.yaml",
    #           "contents": {
    #             "attachment": {
    #               "contentType": "application/yaml",
    #               "encoding": "base64",
    #               "content": "0YMg0LzQtdC90Y8g0L3QtSDQsdGL0LvQviDQv9GA0LjQvNC10YDQsCwg0L/QvtGN0YLQvtC80YMg0YLRg9GCINGN0YLQvtGCINGC0LXQutGB0YIuCtGC0YPRgiDQtNC+0LvQttC10L0g0LHRi9GC0Ywg0L/Qu9C+0YHQutC40Lkg0LTQttGB0L7QvSDQuNC3IH4gMTAg0LrQuC/QstGN0LvRjNGO"
    #             }
    #           }
    #         },
    #         {
    #           "type": "configuration",
    #           "name": "large.yaml",
    #           "contents": {
    #             "attachment": {
    #               "contentType": "application/yaml",
    #               "encoding": "base64",
    #               "content": "0YMg0LzQtdC90Y8g0L3QtSDQsdGL0LvQviDQv9GA0LjQvNC10YDQsCwg0L/QvtGN0YLQvtC80YMg0YLRg9GCINGN0YLQvtGCINGC0LXQutGB0YIuCtGC0YPRgiDQtNC+0LvQttC10L0g0LHRi9GC0Ywg0L/Qu9C+0YHQutC40Lkg0LTQttGB0L7QvSDQuNC3IH4gMTAg0LrQuC/QstGN0LvRjNGO"
    #             }
    #           }
    #         }
    #       ]
    #     }
    #   ]
    # }
import os
import base64
from ..commands.create import get_bom_ref

def discover_standalone_runnable_component(standalone_runnable: dict, resources_dir: str) -> dict:
    if standalone_runnable.get("mime-type") != "application/vnd.qubership.standalone-runnable":
        print("Ignoring. Component mime-type must be 'application/vnd.qubership.standalone-runnable'")
        return standalone_runnable
    if not os.path.isdir(resources_dir):
        raise ValueError(f"Resources directory '{resources_dir}' does not exist or is not a directory")
    config_files = [f for f in os.listdir(resources_dir) if os.path.isfile(os.path.join(resources_dir, f)) and f.endswith(('.yaml', '.yml', '.json'))]
    if not config_files:
        raise ValueError(f"No configuration files found in directory '{resources_dir}'")

    bom_ref = standalone_runnable.get("bom-ref", get_bom_ref(standalone_runnable.get("name")))
    component = {
        "bom-ref": f"{bom_ref}",
        "type": "application",
        "mime-type": "application/vnd.qubership.standalone-runnable",
        "name": standalone_runnable.get("name"),
        "version": standalone_runnable.get("version", "1.0.0"),
        "properties": standalone_runnable.get("properties", []),
        "components": [
            {
                "bom-ref": f"{get_bom_ref('resource-profile-baselines')}",
                "type": "data",
                "mime-type": "application/vnd.qubership.resource-profile-baseline",
                "name": "resource-profile-baselines",
                "data": []
            }
        ]
    }
    for cfg_file in config_files:
        cfg_path = os.path.join(resources_dir, cfg_file)
        with open(cfg_path, "rb") as f:
            content = f.read()
        encoded_content = base64.b64encode(content).decode('utf-8')
        content_type = "application/json" if cfg_file.endswith('.json') else "application/yaml"
        config_entry = {
            "type": "configuration",
            "name": cfg_file,
            "contents": {
                "attachment": {
                    "contentType": content_type,
                    "encoding": "base64",
                    "content": encoded_content
                }
            }
        }
        component["components"][0]["data"].append(config_entry)
    return component
