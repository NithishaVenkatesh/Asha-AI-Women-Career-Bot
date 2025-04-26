FROM python:3.11-slim

WORKDIR /app

COPY . /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

# If you have a main.py or app.py, set your start command later in Railway
# Example:
# CMD ["python", "main.py"]
