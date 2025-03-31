# Use a lightweight Alpine Linux base image
FROM alpine:latest

# Install bash, curl, and jq (required by the script)
RUN apk add --no-cache bash curl jq

# Set default environment variables for Radarr configuration
ENV RADARR_URL="http://localhost:7878" \
    RADARR_API_KEY="your_default_radarr_api_key" \
    MAX_MOVIES="1" \
    SLEEP_DURATION="900" \
    RANDOM_SELECTION="true"

# Copy your radarr-hunter.sh script into the container
COPY radarr-hunter.sh /usr/local/bin/radarr-hunter.sh

# Make the script executable
RUN chmod +x /usr/local/bin/radarr-hunter.sh

# Set the default command to run the script
ENTRYPOINT ["/usr/local/bin/radarr-hunter.sh"]
