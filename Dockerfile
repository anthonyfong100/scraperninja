FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# --- Install system dependencies for Chromium ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxss1 \
    libnss3 \
    libnspr4 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    fonts-liberation \
    xdg-utils \
    ca-certificates \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    libpulse0 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml uv.lock ./

RUN uv run camoufox fetch
RUN uv sync --no-dev

COPY . .
RUN mkdir -p logs/docker

CMD ["bash", "-c", "Xvfb :99 -screen 0 1280x720x24 & export DISPLAY=:99 && uv run --no-sync main.py -o LAX -d JFK --date 2025-12-15 -p 1"]