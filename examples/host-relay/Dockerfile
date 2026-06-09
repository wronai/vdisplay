FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11-apps \
        x11-utils \
        x11-xserver-utils \
        xdotool \
        scrot \
        x11-apps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[pillow]"

COPY examples/common /app/examples/common
COPY examples/host-relay/relay_demo.py ./relay_demo.py

ENV PYTHONPATH=/app/examples/common
ENV VD_OUTPUT_DIR=/output

ENV WINDOW_TITLE=xterm
ENV VD_TARGET=offscreen

CMD ["python", "relay_demo.py"]
