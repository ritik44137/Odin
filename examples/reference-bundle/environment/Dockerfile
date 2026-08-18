FROM python:3.11-slim

# Dependencies are baked in so the rollout needs no network.
RUN pip install --no-cache-dir pytest==8.3.4

WORKDIR /app

# Only the starting state is copied. tests/ and solution/ stay outside the image
# so nothing under /app reveals the held-out cases or the reference fix.
COPY app/ /app/

ENV PYTHONPATH=/app
