from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
import json

from app.auth import router as auth_router
from app.feedback import router as feedback_router
from app.model import router as model_router
from app.user import router as user_router

app = FastAPI(title="Image Prediction API", version="0.0.1")

app.include_router(auth_router.router)
app.include_router(model_router.router)
app.include_router(user_router.router)
app.include_router(feedback_router.router)

@app.middleware("http")
async def round_score_on_predict(request: Request, call_next):
    resp = await call_next(request)

    try:
        if (
            request.url.path == "/model/predict"
            and resp.headers.get("content-type", "").startswith("application/json")
        ):
            body_bytes = b""
            async for chunk in resp.body_iterator:
                body_bytes += chunk

            if not body_bytes:
                return resp

            data = json.loads(body_bytes.decode("utf-8"))

            if isinstance(data, dict) and "score" in data:
                try:
                    data["score"] = round(float(data["score"]), 4)
                except Exception:
                    pass

            return JSONResponse(content=data, status_code=resp.status_code)

    except Exception:
        return resp

    return resp
