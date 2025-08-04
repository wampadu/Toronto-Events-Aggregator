# Use an official Python image
FROM python:3.10-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    curl wget gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libgtk-3-0 \
    libasound2 libxss1 libx11-xcb1 libxext6 libxfixes3 libxrender1 libxkbcommon0 \
    fonts-liberation libappindicator3-1 libdrm2 lsb-release xvfb unzip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    playwright install --with-deps

# Default command (you can change this to test script or real cron job)
CMD ["xvfb-run", "-a", "python", "events_emailer.py"]
