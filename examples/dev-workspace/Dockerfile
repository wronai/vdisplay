FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11-apps \
        x11-utils \
        x11-xserver-utils \
        xdotool \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies are installed at runtime when the repo is mounted,
# but pre-install common dev tools for faster startup.
RUN pip install --no-cache-dir "Pillow>=10.0" pytest

CMD ["bash"]
