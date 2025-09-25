def handle(obj: dict) -> dict:

    # DAO Тут можно добавить логику обработки входящего json Helm Chart

    #print("Running helm_chart handler")
    return {"strategy": "helm", "data": obj}
