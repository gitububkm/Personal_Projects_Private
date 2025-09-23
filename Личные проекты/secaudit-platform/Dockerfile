# Simple Dockerfile for API server
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "secaudit.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
