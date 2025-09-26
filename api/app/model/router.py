import os
from typing import List

from app import db
from app import settings as config
from app import utils
from app.auth.jwt import get_current_user
from app.model.schema import PredictRequest, PredictResponse
from app.model.services import model_predict
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Model"], prefix="/model")


@router.post("/predict")
async def predict(file: UploadFile = File(None), current_user=Depends(get_current_user)):
    rpse = {"success": False, "prediction": None, "score": None, "image_file_name": None}

    # 1) Validación de archivo y extensión
    if file is None or not file.filename or not utils.allowed_file(file.filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type is not supported.")

    # 2) Nombre canónico por hash (no reescribe duplicados)
    new_filename = await utils.get_file_hash(file)
    upload_dir = getattr(config, "UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    dest_path = os.path.join(upload_dir, new_filename)

    # Guardar solo si no existe
    if not os.path.exists(dest_path):
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

    # 3) Invocar servicio de modelo
    try:
        prediction, score = await model_predict(new_filename)
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="File type is not supported",
        )

    # 4) Respuesta
    rpse.update(
        {
            "success": True,
            "prediction": prediction,
            "score": score,
            "image_file_name": new_filename,
        }
    )
    return PredictResponse(**rpse)
