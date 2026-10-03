FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QUESTION_SET_PATH=/app/notebook-questions.json \
    SCENARIO_CONTENT_DIR=/app/scenario-content

WORKDIR /app
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt \
    && useradd --uid 10001 --create-home appuser

COPY web.py catalog.py questions.py scenario.py notebook-questions.json ./
COPY agent/retrieval.py ./agent/retrieval.py
COPY static/ ./static/
COPY scenario-content/ ./scenario-content/
USER 10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "web:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*", "--no-access-log"]
