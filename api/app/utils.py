import hashlib
import os


def allowed_file(filename):
    """
    Allowed: .png, .jpg, .jpeg, .gif (case-insensitive)
    """
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in {"png", "jpg", "jpeg", "gif"}


async def get_file_hash(file):
    """
    MD5 del contenido + extensión original en minúsculas.
    Devuelve <md5>.<ext>
    """
    content = await file.read()
    digest = hashlib.md5(content).hexdigest()
    await file.seek(0)

    _, ext = os.path.splitext(file.filename or "")
    ext = (ext or "").lower().lstrip(".") or "jpg"
    return f"{digest}.{ext}"
