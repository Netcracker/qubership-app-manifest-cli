def handle(obj: dict) -> dict:

    # DAO Тут можно добавить логику обработки входящего json  Docker Image

    #print("Running docker_image handler")
    return {"strategy": "docker", "data": obj}
