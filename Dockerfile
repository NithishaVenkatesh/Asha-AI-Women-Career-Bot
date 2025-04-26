FROM python:3.11-slim

WORKDIR /app

COPY . /app/

RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

# Optional: define start command
# CMD ["python", "main.py"]
