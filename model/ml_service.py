import json
import os
import time

import numpy as np
import redis
import settings
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import decode_predictions, preprocess_input
from tensorflow.keras.preprocessing import image

db = redis.StrictRedis(
    host=settings.REDIS_IP,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB_ID,
    decode_responses=True,
)

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
    img_path = os.path.join(settings.UPLOAD_FOLDER, image_name)

    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    preds = model.predict(x)
    top1 = decode_predictions(preds, top=1)[0][0]
    class_name = top1[1]
    pred_probability = float(np.round(top1[2], 4))

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
        _, job_json = db.brpop(settings.REDIS_QUEUE)

        job = json.loads(job_json)

        job_id = job.get("id") or job.get("job_id")

        image_name = job.get("image_name") or job.get("image_file_name")

        try:
            class_name, pred_probability = predict(image_name)
            output = {"prediction": class_name, "score": float(pred_probability)}
        except Exception:

            output = {"prediction": "error", "score": 0.0}

        db.set(job_id, json.dumps(output))

        time.sleep(settings.SERVER_SLEEP)


if __name__ == "__main__":
    print("Launching ML service...")
    classify_process()
