# Image utilisée UNIQUEMENT en local (docker compose) pour simuler le déclencheur SQS.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY handler.py local_runner.py ./
CMD ["python", "-u", "local_runner.py"]
