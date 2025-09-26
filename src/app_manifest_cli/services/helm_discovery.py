import base64
import os
import subprocess
import sys
import yaml
from typing import List
from ..commands.create import get_bom_ref
from ..services.purl_url import url_2_purl
# Здесь должны быть методы для работы с helm chart
# для генерации дополнительных метаданных
# На входе получаем url чарта
# командами helm скачиваем чарт
# распаковываем его
# 1. Читаем Chart.yaml, чтобы:
# - узнать его type, если type: library, то добавляем в манифест property isLibrary=true
# - узнать, есть ли у него dependencies, если есть, то для каждой зависимости добавляем вложенную component в компоненту этого чарта в манифесте
# 2. Проверяем,есть ли в чарте файл с именем values.schema.json
# если есть, то шифруем файл в base64 и добавляем в component чарта вложенный объект
#       "components": [
#        {
#          "bom-ref": "qubership-jaeger-values-schema:7f17a6dc-b973-438f-abb7-e0c57a32afc5",
#          "type": "data",
#          "mime-type": "application/vnd.qubership.helm.values.schema",
#          "name": "values.schema.json",
#          "data": [
#            {
#              "type": "configuration",
#              "name": "values.schema.json",
#              "contents": {
#                "attachment": {
#                  "contentType": "application/json",
#                  "encoding": "base64",
#                  "content": "ewogICIkc2NoZW1hIjogImh0dHA6Ly9qc29uLXNjaGVtYS5vcmcvZHJhZnQtMDcvc2NoZW1hIyIsCiAgInR5cGUiOiAib2JqZWN0IiwKICAicHJvcGVydGllcyI6IHsKICAgICJpbWFnZXMiOiB7CiAgICAgICJ0eXBlIjogIm9iamVjdCIsCiAgICAgICJwcm9wZXJ0aWVzIjogewogICAgICAgICJqYWVnZXIiOiB7CiAgICAgICAgICAidHlwZSI6ICJvYmplY3QiLAogICAgICAgICAgInByb3BlcnRpZXMiOiB7CiAgICAgICAgICAgICJyZXBvc2l0b3J5IjogeyAidHlwZSI6ICJzdHJpbmciIH0sCiAgICAgICAgICAgICJ0YWciOiB7ICJ0eXBlIjogInN0cmluZyIgfSwKICAgICAgICAgICAgInB1bGxQb2xpY3kiOiB7ICJ0eXBlIjogInN0cmluZyIgfQogICAgICAgICAgfQogICAgICAgIH0sCiAgICAgICAgImVudm95IjogewogICAgICAgICAgInR5cGUiOiAib2JqZWN0IiwKICAgICAgICAgICJwcm9wZXJ0aWVzIjogewogICAgICAgICAgICAicmVwb3NpdG9yeSI6IHsgInR5cGUiOiAic3RyaW5nIiB9LAogICAgICAgICAgICAidGFnIjogeyAidHlwZSI6ICJzdHJpbmciIH0KICAgICAgICAgIH0KICAgICAgICB9CiAgICAgIH0KICAgIH0KICB9Cn0="
#                }
#              }
#            }
#          ]
#        }
#      ]
# 3. Проверяем, есть ли в чарте директория resource-profiles
# если есть, то для каждого файла с расширением .yaml, .yml или .json в этой директории
# шифруем файл в base64 и добавляем в component чарта вложенный объект
#       {
#          "bom-ref": "resource-profile-baselines:61439a11-c00d-43f5-9bae-fe6db05db2d5",
#          "type": "data",
#          "mime-type": "application/vnd.qubership.resource-profile-baseline",
#          "name": "resource-profile-baselines",
#          "data": [
#            {
#              "type": "configuration",
#              "name": "config.yaml",
#              "contents": {
#                "attachment": {
#                  "contentType": "application/yaml",
#                  "encoding": "base64",
#                  "content": "0YMg0LzQtdC90Y8g0L3QtSDQsdGL0LvQviDQv9GA0LjQvNC10YDQsCwg0L"
#                }
#              }
#            },
#            ]
#        }


def helm_discovery(components: List) -> List:
    if components is None:
        return {}
    # Проверяю, что helm установлен
    try:
        subprocess.run("helm version", shell=True, text=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print("Helm is not installed or not found in PATH. Please install Helm to use helm discovery.", file=sys.stderr)
        return components
    print("Helm is installed, proceeding with helm discovery.")
    # Иду по всем компонентам, у которых mime-type application/vnd.qubership.helm.chart
    for comp in [f for f in components if f['mime-type'] == 'application/vnd.qubership.helm.chart']:
        chart = single_chart_discovery(comp)
        comp.update(chart)
    return components

def single_chart_discovery(chart: dict) -> dict:
        try:
            # делаю директорию для скачивания чарта с рандомным именем
            chart_dir = f"chart-{os.urandom(4).hex()}"
            os.makedirs(chart_dir, exist_ok=True)
            if chart.get("mime-type") != "application/vnd.qubership.helm.chart":
                print(f"Component {chart['name']} isn't a chart.")
                return chart
            if not chart['reference']:
                raise ValueError("Helm chart component must have reference")
            # Тут должна быть логика скачивания чарта по purl, распаковки и чтения файлов
            chart_url = chart["reference"]
            print(f"Discovering helm chart: {chart['name']} with reference: {chart['reference']}")
            try:
                helm_output = subprocess.run(f"helm pull --untar --untardir {chart_dir} {chart_url}", shell=True, text=True, check=True, capture_output=True).stdout.split()
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Error pulling chart for {chart['name']} with reference: {chart['reference']}. Error: {e.stderr}")
            chart_file_path = os.path.join(chart_dir, chart['name'], "Chart.yaml")
            if not os.path.isfile(chart_file_path):
                raise ValueError(f"Chart.yaml not found in pulled chart for {chart['name']}")
            with open(chart_file_path, 'r') as f:
                chart_info = yaml.safe_load(f)
            #print(f"Chart info: {chart_info}")
            if chart_info.get("type") == "library":
                if "properties" not in chart:
                    chart["properties"] = []
                chart["properties"].append({"name": "isLibrary", "value": True})
            # Проверяю наличие dependencies
            if "dependencies" not in chart_info:
                print(f"No dependencies found in chart {chart['name']}")
                # continue
            for dep in chart_info.get("dependencies", []):
                if "name" not in dep or "version" not in dep:
                    print(f"Skipping invalid dependency in chart {chart['name']}: {dep}")
                    continue
                dep_bom_ref = get_bom_ref(dep["name"])
                if "components" not in chart:
                    chart["components"] = []
                chart["components"].append({
                    "bom-ref": f"{dep_bom_ref}",
                    "type": "application",
                    "mime-type": "application/vnd.qubership.helm.chart",
                    "name": dep["name"],
                    "version": dep["version"],
                    "properties": [],
                    "components": []
                })
            # Проверяю наличие values.schema.json
            if os.path.isfile(os.path.join(chart_dir, chart['name'], "values.schema.json")):
                with open(os.path.join(chart_dir, chart['name'], "values.schema.json"), 'rb') as f:
                    encoded_content = base64.b64encode(f.read()).decode('utf-8')
                if "components" not in chart:
                    chart["components"] = []
                chart["components"].append({
                    "bom-ref": get_bom_ref(f"{chart['name']}-values-schema"),
                    "type": "data",
                    "mime-type": "application/vnd.qubership.helm.values.schema",
                    "name": "values.schema.json",
                    "data": [{
                        "type": "configuration",
                        "name": "values.schema.json",
                        "contents": {
                            "attachment": {
                                "contentType": "application/json",
                                "encoding": "base64",
                                "content": encoded_content
                            }
                        }
                    }]
                })
            # Проверяю наличие resource-profiles directory
            resource_profiles_path = os.path.join(chart_dir, chart['name'], "resource-profiles")
            if os.path.isdir(resource_profiles_path):
                profile_files = [f for f in os.listdir(resource_profiles_path) if os.path.isfile(os.path.join(resource_profiles_path, f)) and f.endswith(('.yaml', '.yml', '.json'))]
                if profile_files:
                    if "components" not in chart:
                        chart["components"] = []
                    chart["components"].append({
                        "bom-ref": get_bom_ref("resource-profile-baselines"),
                        "type": "data",
                        "mime-type": "application/vnd.qubership.resource-profile-baseline",
                        "name": "resource-profile-baselines",
                        "data": []
                    })
                    for profile_file in profile_files:
                        profile_path = os.path.join(resource_profiles_path, profile_file)
                        with open(profile_path, 'rb') as f:
                            content = f.read()
                        encoded_content = base64.b64encode(content).decode('utf-8')
                        content_type = "application/json" if profile_file.endswith('.json') else "application/yaml"
                        chart["components"][-1]["data"].append({
                            "type": "configuration",
                            "name": profile_file,
                            "contents": {
                                "attachment": {
                                    "contentType": content_type,
                                    "encoding": "base64",
                                    "content": encoded_content
                                }
                            }
                        })
        except Exception as e:
            print(f"Error processing helm chart component {chart.get('name', 'unknown')}: {e}", file=sys.stderr)
        finally:
            # Удаляю директорию чарта
            if os.path.isdir(chart_dir):
                subprocess.run(f"rm -rf {chart_dir}", shell=True)
        return chart
