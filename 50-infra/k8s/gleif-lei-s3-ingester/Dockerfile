FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir boto3 psycopg2-binary

WORKDIR /app
COPY ingester.py /app/ingester.py

ENTRYPOINT ["python", "/app/ingester.py"]
