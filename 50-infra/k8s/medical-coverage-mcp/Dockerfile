FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir "kubernetes>=31.0.0" "psycopg[binary]>=3.2.0"

WORKDIR /app
COPY mcp_server.py /app/mcp_server.py

EXPOSE 8080
CMD ["python", "/app/mcp_server.py"]
