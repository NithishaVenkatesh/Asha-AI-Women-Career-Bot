FROM python:3.11-slim

WORKDIR /app

COPY . /app/

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

# Example start command (change to your app's main file if needed)
# CMD ["python", "main.py"]
