# Use a lightweight Alpine Linux base image
FROM alpine:latest

# Install required dependencies
RUN apk add --no-cache \
    bash \
    curl \
    jq

# Set default environment variables
ENV API_KEY="your-api-key" \
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
COPY huntarr.sh /usr/local/bin/huntarr.sh

# Make the script executable
RUN chmod +x /usr/local/bin/huntarr.sh

# Set the default command to run the script
ENTRYPOINT ["/usr/local/bin/huntarr.sh"]

# Add labels for better container management
LABEL maintainer="PlexGuide" \
      description="Huntarr [Radarr Edition] - Automates finding missing movies and quality upgrades" \
      version="7.0" \
      url="https://github.com/plexguide/Huntarr-Radarr"
