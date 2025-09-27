# stress_test/locustfile.py
import os

from locust import HttpUser, between, task
from requests_toolbelt.multipart.encoder import MultipartEncoder


class APIUser(HttpUser):
    """
    Load user that:
    - logs in on start and stores a JWT token
    - hits "/" (or "/docs" if "/" is missing)
    - posts an image to /model/predict with Authorization header
    """

    wait_time = between(0.2, 1.0)
    token: str = ""

    def on_start(self):
        """Authenticate and keep the token."""
        data = {
            "grant_type": "",
            "username": "admin@example.com",
            "password": "admin",
            "scope": "",
            "client_id": "",
            "client_secret": "",
        }
        with self.client.post(
            "/login", data=data, name="/login", catch_response=True
        ) as r:
            if r.status_code == 200:
                self.token = r.json().get("access_token", "")
                if not self.token:
                    r.failure("Missing access_token in response")
            else:
                r.failure(f"Login failed with status {r.status_code}")

    @task(1)
    def index(self):
        """Try / and fall back to /docs if not found."""
        with self.client.get("/", name="/", catch_response=True) as r:
            if r.status_code == 404:
                self.client.get("/docs", name="/docs")

    @task(3)
    def predict(self):
        """Send dog.jpeg to /model/predict."""
        if not self.token:
            return  # skip if login failed

        img_path = self._find_image()
        with open(img_path, "rb") as f:
            mp = MultipartEncoder(fields={"file": ("dog.jpeg", f, "image/jpeg")})
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": mp.content_type,
            }
            self.client.post(
                "/model/predict",
                data=mp,
                headers=headers,
                name="/model/predict",
            )

    def _find_image(self) -> str:
        """Look for stress_test/dog.jpeg, else fall back to tests/dog.jpeg."""
        here = os.path.dirname(__file__)
        candidate = os.path.join(here, "dog.jpeg")
        if os.path.exists(candidate):
            return candidate
        # fallback: project_root/tests/dog.jpeg
        return os.path.join(os.path.dirname(here), "tests", "dog.jpeg")
