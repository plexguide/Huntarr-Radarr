# Start from a lightweight Python image
FROM python:3.10-slim

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

# Create a directory for our script and state files
RUN mkdir -p /app && mkdir -p /tmp/huntarr-radarr-state

# Switch working directory
WORKDIR /app

# Install any Python dependencies you need for the script
# (requests is used in your code, so we explicitly install it)
RUN pip install --no-cache-dir requests

# Copy the Python script into the container
COPY huntarr.py /app/huntarr.py

# Make the script executable (optional, but good practice)
RUN chmod +x /app/huntarr.py

# Add a simple HEALTHCHECK (this is optional)
HEALTHCHECK --interval=5m --timeout=3s \
  CMD pgrep -f huntarr.py || exit 1

# The script’s entrypoint. It will run your `huntarr.py` when the container starts.
ENTRYPOINT ["python", "huntarr.py"]
