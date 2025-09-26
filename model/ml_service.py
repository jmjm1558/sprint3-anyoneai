import json
import os
import time

import numpy as np
import redis
import settings
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import decode_predictions, preprocess_input
from tensorflow.keras.preprocessing import image

# Conexión a Redis usando la configuración de settings.py
db = redis.StrictRedis(
    host=settings.REDIS_IP,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB_ID,
    decode_responses=True,  # trabajamos con str en lugar de bytes
)

# Carga del modelo (una sola vez por proceso)
model = ResNet50(weights="imagenet")


def predict(image_name):
    """
    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.

    Parameters
    ----------
    image_name : str
        Image filename.

    Returns
    -------
    class_name, pred_probability : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """
    # Ruta a la imagen dentro de la carpeta de uploads
    img_path = os.path.join(settings.UPLOAD_FOLDER, image_name)

    # Cargar imagen y preprocesar para ResNet50
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    # Predicción y decodificación top-1
    preds = model.predict(x)
    top1 = decode_predictions(preds, top=1)[0][0]  # (class_id, label, prob)
    class_name = top1[1]
    pred_probability = float(np.round(top1[2], 4))  # convertir a float y redondear

    return class_name, pred_probability


def classify_process():
    """
    Loop indefinitely asking Redis for new jobs.
    When a new job arrives, takes it from the Redis queue, uses the loaded ML
    model to get predictions and stores the results back in Redis using
    the original job ID so other services can see it was processed and access
    the results.
    """
    while True:
        # 1) Tomar un nuevo job desde Redis (bloquea hasta que llegue uno)
        _, job_json = db.brpop(settings.REDIS_QUEUE)

        # 2) Decodificar datos del job
        job = json.loads(job_json)

        # 3) Conservar el ID original del job
        job_id = job.get("id") or job.get("job_id")

        # 4) Obtener nombre de la imagen
        image_name = job.get("image_name") or job.get("image_file_name")

        # 5) Ejecutar predicción
        try:
            class_name, pred_probability = predict(image_name)
            output = {"prediction": class_name, "score": float(pred_probability)}
        except Exception:
            # Resultado mínimo ante error (por ejemplo, imagen inexistente)
            output = {"prediction": "error", "score": 0.0}

        # 6) Guardar resultado en Redis usando la clave del job original
        db.set(job_id, json.dumps(output))

        # 7) Pausa breve
        time.sleep(settings.SERVER_SLEEP)


if __name__ == "__main__":
    # Now launch process
    print("Launching ML service...")
    classify_process()
