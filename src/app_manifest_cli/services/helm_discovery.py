import sys
import os

# Добавляю в sys.path путь к корню проекта, чтобы можно было импортировать внутренние модули
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

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
# 3. Проверяем, есть ли в чарте директория configurations и в ней есть файлы *.yaml
# тогда добавляем новый компонент в манифест с mime-type application/vnd.qubership.standalone-runnable
# для каждого файла *.yaml в этой директории добавляем вложенный объект в этот компонент
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

import yaml
import json
from typing import List

def helm_discovery(components: List) -> dict:
    if components is None:
        return {}
    for comp in components:
        if comp.get("mime-type") != "application/vnd.qubership.helm.chart":
            continue
        if not comp.purl:
            raise ValueError("Helm chart component must have purl")
        # Тут должна быть логика скачивания чарта по purl, распаковки и чтения файлов
        # Пока что просто заглушка
        print(f"Discovering helm chart: {comp['name']} with purl: {comp['purl']}")
        # Пример добавления свойства isLibrary=true, если в Chart.yaml type: library
        # comp['properties'].append({"name": "isLibrary", "value": True})
        # Пример добавления вложенного компонента для values.schema.json
        # comp['components'].append({
        #     "bom-ref": "example-values-schema",
        #     "type": "data",
        #     "mime-type": "application/vnd.qubership.helm.values.schema",
        #     "name": "values.schema.json",
        #     "data": [{
        #         "type": "configuration",
        #         "name": "values.schema.json",
        #         "contents": {
        #             "attachment": {
        #                 "contentType": "application/json",
        #                 "encoding": "base64",
        #                 "content": "base64-encoded-content"
        #             }
        #         }
        #     }]
        # })
        # Пример добавления standalone-runnable компонента для конфигураций из директории configurations
        # comp['components'].append({
        #     "bom-ref": "example-standalone-runnable",
        #     "type": "application",
        #     "mime-type": "application/vnd.qubership.standalone-runnable",
        #     "name": "example-standalone-runnable",
        #     "version": "1.0.0",
        #     "properties": [],
        #     "components": [{
        #         "bom-ref": "example-configuration",
        #         "type": "data",
        #         "mime-type": "application/vnd.qubership.resource-profile-baseline",
        #         "name": "resource-profile-baselines",
        #         "data": [{
        #             "type": "configuration",
        #             "name": "small.yaml",
        #             "contents": {
        #                 "attachment": {
        #                     "contentType": "application/yaml",
        #                     "encoding": "base64",
        #                     "content": "base64-encoded-content"
        #                 }
        #             }
        #         }]
        #     }]
        # })
    return components