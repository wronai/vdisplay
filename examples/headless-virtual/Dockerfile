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

COPY examples/common /app/examples/common
COPY examples/headless-virtual/run_virtual.py ./run_virtual.py

ENV PYTHONPATH=/app/examples/common

ENV VD_OUTPUT_DIR=/output
ENV VD_WIDTH=1280
ENV VD_HEIGHT=720
ENV VD_DISPLAY=:99

CMD ["python", "run_virtual.py"]
