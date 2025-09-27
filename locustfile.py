from pathlib import Path

from locust import HttpUser, between, task


class ImageAPIUser(HttpUser):
    wait_time = between(0.1, 0.5)
    token = None
    image_path = Path(__file__).parent / "tests" / "dog.jpeg"

    def on_start(self):
        data = {
            "grant_type": "",
            "username": "admin@example.com",
            "password": "admin",
            "scope": "",
            "client_id": "",
            "client_secret": "",
        }
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        with self.client.post(
            "/login", data=data, headers=headers, catch_response=True
        ) as r:
            if r.status_code == 200:
                self.token = r.json().get("access_token")
                if self.token:
                    r.success()
                else:
                    r.failure(f"login ok pero sin token: {r.text}")
            else:
                r.failure(f"login {r.status_code}: {r.text}")

    @task
    def predict(self):
        if not self.token:
            self.environment.events.request.fire(
                request_type="POST",
                name="/model/predict",
                response_time=0,
                response_length=0,
                exception=Exception("no token"),
                context={},
            )
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        with self.image_path.open("rb") as f:
            files = {"file": ("dog.jpeg", f, "image/jpeg")}
            with self.client.post(
                "/model/predict",
                headers=headers,
                files=files,
                name="/model/predict",
                catch_response=True,
            ) as r:
                if r.status_code == 200:
                    data = r.json()
                    if data.get("success") is True:
                        r.success()
                    else:
                        r.failure(f"success!=True: {data}")
                else:
                    r.failure(f"{r.status_code}: {r.text}")
