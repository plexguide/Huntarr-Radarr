FROM python:3.9-slim
WORKDIR /app
# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy application files
COPY main.py config.py api.py state.py ./
COPY missing.py upgrade.py ./
COPY utils/ ./utils/
# Create state directory
RUN mkdir -p /tmp/huntarr-state
# Default environment variables
ENV API_KEY="your-api-key" \
    API_URL="http://your-radarr-address:7878" \
    API_TIMEOUT="60" \
    HUNT_MISSING_MOVIES=1 \
    HUNT_UPGRADE_MOVIES=5 \
    SLEEP_DURATION=900 \
    STATE_RESET_INTERVAL_HOURS=168 \
    RANDOM_SELECTION="true" \
    MONITORED_ONLY="true" \
    DEBUG_MODE="false"
# Run the application
CMD ["python", "main.py"]