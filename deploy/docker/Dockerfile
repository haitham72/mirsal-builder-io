# One image for the hosted app: the engine (loopback only) + the FastAPI gateway in front of it, or the worker. Build context = the repository root:
#   docker build -f deploy/docker/Dockerfile -t mirsal .
# ffmpeg with libvpx-vp9 is not optional (the stickers are WEBM/VP9 with alpha): the build FAILS if the encoder is missing.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/* \
 && ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libvpx-vp9

WORKDIR /app
COPY mirsal/requirements.txt mirsal/requirements.txt
COPY deploy/gateway/requirements.txt deploy/gateway/requirements.txt
RUN pip install --no-cache-dir -r mirsal/requirements.txt -r deploy/gateway/requirements.txt

COPY mirsal mirsal
COPY deploy deploy
COPY docs docs

RUN useradd --create-home --uid 10001 app && mkdir -p /data/out /data/in && chown -R app /data /app
USER app
ENV PYTHONUNBUFFERED=1 \
    MIRSAL_OUT=/data/out \
    MIRSAL_INPUT=/data/in \
    MIRSAL_ENGINE_URL=http://127.0.0.1:8789 \
    MIRSAL_JOB_MODE=queue
EXPOSE 8080
# MODE=web (default): engine on 127.0.0.1:8789 + gateway on $PORT.  MODE=worker: `python -m mirsal worker`.  Either one exits when its child dies, so the platform restarts the box.
CMD ["python", "deploy/docker/start.py"]
