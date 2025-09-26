import os
import io
import requests
import streamlit as st
from PIL import Image


# ---------- Config API ----------
def _api_base_url() -> str:
    # Prioridad: API_BASE_URL -> API_HOST/API_PORT -> localhost:8000
    base = os.getenv("API_BASE_URL")
    if not base:
        host = os.getenv("API_HOST", "localhost")
        port = os.getenv("API_PORT", "8000")
        base = f"http://{host}:{port}"
    return base.rstrip("/")


def api(path: str) -> str:
    return f"{_api_base_url()}{path}"


# ---------- Low-level calls ----------
def api_login(username: str, password: str):
    try:
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "",
            "username": username,
            "password": password,
            "scope": "",
            "client_id": "",
            "client_secret": "",
        }
        r = requests.post(api("/login"), headers=headers, data=data, timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token"), None
        return None, f"Login inválido ({r.status_code}): {r.text}"
    except requests.RequestException as e:
        return None, f"No se pudo conectar con la API: {e}"


def api_predict(token: str, file_name: str, file_bytes: bytes):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        files = [("file", (file_name, io.BytesIO(file_bytes), "image/jpeg"))]
        r = requests.post(api("/model/predict"), headers=headers, files=files, timeout=30)
        if r.status_code == 200:
            return r.json(), None
        return None, f"Error {r.status_code}: {r.text}"
    except requests.RequestException as e:
        return None, f"No se pudo conectar con la API: {e}"


def api_feedback(token: str, payload: dict):
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        r = requests.post(api("/feedback/"), headers=headers, json=payload, timeout=10)
        if r.status_code in (200, 201):
            return r.json(), None
        return None, f"Error {r.status_code}: {r.text}"
    except requests.RequestException as e:
        return None, f"No se pudo conectar con la API: {e}"


# ---------- UI ----------
st.set_page_config(page_title="Image Classifier", page_icon="🐶", layout="centered")

st.title("🐶 Image Classifier UI")

if "token" not in st.session_state:
    st.session_state.token = None

with st.sidebar:
    st.subheader("API")
    st.code(_api_base_url())

if st.session_state.token is None:
    st.subheader("Login")
    email = st.text_input("Email", "admin@example.com")
    password = st.text_input("Password", type="password", value="admin")
    if st.button("Ingresar", type="primary"):
        token, err = api_login(email, password)
        if token:
            st.session_state.token = token
            st.success("✅ Login correcto")
            st.rerun()
        else:
            st.error(err or "Credenciales inválidas")
else:
    st.success("Sesión iniciada ✅")
    if st.button("Cerrar sesión"):
        st.session_state.token = None
        st.rerun()

    st.divider()
    st.subheader("Predicción")

    file = st.file_uploader("Subí una imagen", type=["jpg", "jpeg", "png"])
    if file:
        img = Image.open(file).convert("RGB")
        st.image(img, caption=file.name, use_container_width=True)

        if st.button("🚀 Predecir", type="primary"):
            data, err = api_predict(st.session_state.token, file.name, file.getvalue())
            if err:
                st.error(err)
            else:
                st.session_state.last_prediction = data
                st.json(data)

    st.divider()
    st.subheader("Feedback")
    if "last_prediction" in st.session_state:
        pred = st.session_state.last_prediction
        suggested = pred.get("prediction")
        score = pred.get("score")

        correct = st.selectbox("¿La predicción fue correcta?", ["Sí", "No"])
        true_label = st.text_input("Etiqueta correcta (si no fue correcta)", "" if correct == "Sí" else suggested or "")
        notes = st.text_area("Notas (opcional)")

        if st.button("Enviar feedback"):
            payload = {
                "prediction": suggested,
                "score": score,
                "is_correct": (correct == "Sí"),
                "true_label": true_label if correct == "No" else suggested,
                "notes": notes,
            }
            _, err = api_feedback(st.session_state.token, payload)
            if err:
                st.error(err)
            else:
                st.success("Gracias por el feedback 🙌")
    else:
        st.info("Hacé una predicción primero para poder enviar feedback.")
