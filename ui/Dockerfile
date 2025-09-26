FROM python:3.8.13 AS base

ENV PYTHONPATH=/src

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./ /src/

FROM base AS test
RUN ["python", "-m", "pytest", "-v", "tests"]

FROM base AS build
CMD ["streamlit", "run", "app/image_classifier_app.py", "--server.port=9090", "--server.address=0.0.0.0"]
