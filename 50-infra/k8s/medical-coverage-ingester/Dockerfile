FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir boto3 requests

WORKDIR /app
COPY kotoba_datomic.py /app/kotoba_datomic.py
COPY ingester.py /app/ingester.py

ENTRYPOINT ["python", "/app/ingester.py"]
