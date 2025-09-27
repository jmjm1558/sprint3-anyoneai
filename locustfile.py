from locust import HttpUser, between, task

BASE = "http://localhost:8000"
PREDICT = "/api/predict"  # <-- CAMBIA a la ruta real que viste en el código
USE_JSON = True  # <-- Pon False si tu endpoint usa archivo
FILE_PATH = r".\uploads\sample.jpg"  # <-- Cambia solo si USE_JSON=False
JSON_BODY = {"text": "hola"}  # <-- Cambia a los campos MÍNIMOS reales si es JSON


class ApiUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def predict(self):
        if USE_JSON:
            self.client.post(PREDICT, json=JSON_BODY, name="/predict")
        else:
            with open(FILE_PATH, "rb") as f:
                # Si en tu código el parámetro es, por ejemplo, image: UploadFile = File(...),
                # cambia "file" por "image".
                self.client.post(PREDICT, files={"file": f}, name="/predict")
