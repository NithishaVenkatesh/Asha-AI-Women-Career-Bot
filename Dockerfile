FROM python:3.11-slim

# (optional but good)
WORKDIR /app

# Copy your code
COPY . /app/.

# Install deps
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

# Then continue your build...
