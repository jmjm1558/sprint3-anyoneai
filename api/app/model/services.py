import json
import time
from uuid import uuid4

import redis

from .. import settings

# conection to Redis using settings from settings.py
db = redis.Redis(
    host=settings.REDIS_IP,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB_ID,
)

async def model_predict(image_name):
    print(f"Processing image {image_name}...")
    prediction = None
    score = None

    # ID único del job
    job_id = str(uuid4())

    # Datos del job
    job_data = {"id": job_id, "image_name": image_name}

    # Encolar trabajo
    db.lpush(settings.REDIS_QUEUE, json.dumps(job_data))

    # Polling hasta obtener resultado o timeout
    start = time.monotonic()
    timeout_s = getattr(settings, "API_SLEEP_TIMEOUT", 45)

    while True:
        # Intentar leer resultado (JSON string) en la clave job_id
        output = db.get(job_id)

        if output is not None:
            output = json.loads(output.decode("utf-8"))
            prediction = output["prediction"]
            score = output["score"]

            db.delete(job_id)
            break

        if time.monotonic() - start > timeout_s:
            # Salimos por timeout controlado
            raise TimeoutError("Model prediction timed out")

        time.sleep(getattr(settings, "API_SLEEP", 0.1))

    return prediction, score
