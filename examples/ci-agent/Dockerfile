FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11-utils \
        x11-xserver-utils \
        xdotool \
        x11-apps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[pillow]"

COPY examples/ci-agent/agent.py ./agent.py

ENV VD_OUTPUT_DIR=/output
ENV VD_FRAMES=3
ENV VD_WIDTH=1920
ENV VD_HEIGHT=1080
ENV VD_DISPLAY=:99

CMD ["python", "agent.py"]
