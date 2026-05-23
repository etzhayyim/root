FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

# Copy source first so editable install can resolve the package
COPY pyproject.toml .
COPY src/ src/
RUN uv pip install --system -e .

ENV PORT=8000
EXPOSE 8000

CMD ["python", "-m", "browser_agent.server"]
