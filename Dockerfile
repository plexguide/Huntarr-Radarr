FROM python:3.11-alpine

LABEL maintainer="PlexGuide" \
      description="Huntarr [Radarr Edition] - Automates finding missing movies and quality upgrades" \
      version="8.0" \
      url="https://github.com/plexguide/Huntarr-Radarr"

# Install required dependencies
RUN pip install --no-cache-dir requests

# Set default environment variables
ENV API_KEY="" \
    API_URL="http://your-radarr-address:7878" \
    SEARCH_TYPE="both" \
    MAX_MISSING="1" \
    MAX_UPGRADES="5" \
    SLEEP_DURATION="900" \
    RANDOM_SELECTION="true" \
    MONITORED_ONLY="true" \
    STATE_RESET_INTERVAL_HOURS="168" \
    DEBUG_MODE="false"

# Create state directory
RUN mkdir -p /tmp/huntarr-radarr-state

# Copy the script into the container
COPY huntarr.py /app/huntarr.py

# Make the script executable
RUN chmod +x /app/huntarr.py

# Set working directory
WORKDIR /app

# Set the default command to run the script
ENTRYPOINT ["python", "huntarr.py"]

# Add health check
HEALTHCHECK --interval=5m --timeout=3s \
  CMD ps aux | grep python | grep huntarr.py || exit 1