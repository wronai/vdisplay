FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11-apps \
        x11-utils \
        x11-xserver-utils \
        xdotool \
        scrot \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[pillow]"

COPY examples/host-mirror/mirror_demo.py ./mirror_demo.py

ENV VD_OUTPUT_DIR=/output
ENV VD_SOURCE=primary

CMD ["python", "mirror_demo.py"]
