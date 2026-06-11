FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    asyncpg==0.29.0 \
    aiohttp==3.10.11 \
    fastapi==0.115.6 \
    "uvicorn[standard]==0.34.0" \
    beautifulsoup4==4.12.3 \
    lxml==5.3.0 \
    pdfplumber==0.11.4 \
    openpyxl==3.1.5 \
    python-docx==1.1.2

WORKDIR /app
COPY worker.py /app/worker.py

EXPOSE 8080
CMD ["python", "/app/worker.py"]
