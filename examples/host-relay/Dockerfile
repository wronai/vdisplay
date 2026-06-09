FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11-apps \
        x11-utils \
        x11-xserver-utils \
        xdotool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[pillow]"

COPY examples/host-relay/relay_demo.py ./relay_demo.py

ENV WINDOW_TITLE=xterm
ENV VD_TARGET=offscreen

CMD ["python", "relay_demo.py"]
