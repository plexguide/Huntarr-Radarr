# Radarr Hunter - Force Radarr to Hunt Missing Movies

<h2 align="center">Want to Help? Click the Star in the Upper-Right Corner! ⭐</h2>

![image](https://github.com/user-attachments/assets/c5f54723-6828-4633-8c9c-54f25f4a1e9c)

**NOTE**: This utilizes Radarr API Version - `3`. The Script: [radarr-hunter.sh](radarr-hunter.sh)

## Table of Contents
- [Overview](#overview)
- [Related Projects](#related-projects)
- [Features](#features)
- [How It Works](#how-it-works)
- [Configuration Options](#configuration-options)
- [Installation Methods](#installation-methods)
  - [Docker Run](#docker-run)
  - [Docker Compose](#docker-compose)
  - [Unraid Users](#unraid-users)
  - [SystemD Service](#systemd-service)
- [Use Cases](#use-cases)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)

## Overview

This script continually searches your Radarr library specifically for movies that are missing (monitored but not downloaded) and automatically triggers searches for those missing movies. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your movie collection.

## Related Projects

* [Sonarr Hunter](https://github.com/plexguide/Sonarr-Hunter) - Sister version for TV shows
* [Lidarr Hunter](https://github.com/plexguide/Lidarr-Hunter) - Sister version for music
* [Unraid Intel ARC Deployment](https://github.com/plexguide/Unraid_Intel-ARC_Deployment) - Convert videos to AV1 Format (I've saved 325TB encoding to AV1)
* Visit [PlexGuide](https://plexguide.com) for more great scripts

## Features

- 🔄 **Continuous Operation**: Runs indefinitely until manually stopped
- 🎯 **Direct Missing Movie Targeting**: Directly identifies and processes only missing movies
- 🎲 **Random Selection**: By default, selects missing movies randomly to distribute searches across your library
- ⏱️ **Throttled Searches**: Includes configurable delays to prevent overloading indexers
- 📊 **Status Reporting**: Provides clear feedback about what it's doing and which movies it's searching for
- 🛡️ **Error Handling**: Gracefully handles connection issues and API failures

## How It Works

1. **Initialization**: Connects to your Radarr instance and retrieves a list of only monitored movies without files
2. **Selection Process**: Randomly selects a missing movie from the filtered list
3. **Refresh**: Refreshes the metadata for the selected movie
4. **Search Trigger**: Uses the MoviesSearch command to instruct Radarr to search for the missing movie
5. **Rescan**: Rescans the movie folder to detect any new downloads
6. **Throttling**: After processing a movie, it pauses for a configurable amount of time
7. **Cycling**: After processing the configured number of movies, it starts a new cycle, refreshing the missing movie data

## Configuration Options

The following environment variables can be configured:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | Your Radarr API key | Required |
| `API_URL` | URL to your Radarr instance | Required |
| `MAX_MOVIES` | Movies to process before restarting cycle | 1 |
| `SLEEP_DURATION` | Seconds to wait after processing a movie (600=10min) | 600 |
| `REFRESH_DURATION` | Pause between multiple movies if MAX_MOVIES > 1 (mini sleep) | 30 |
| `RANDOM_SELECTION` | Use random selection (`true`) or sequential (`false`) | true |

## Installation Methods

### Docker Run

The simplest way to run Radarr Hunter is via Docker:

```bash
docker run -d --name radarr-hunter \
  --restart always \
  -e API_KEY="your-api-key" \
  -e API_URL="http://your-radarr-address:7878" \
  -e MAX_MOVIES="1" \
  -e SLEEP_DURATION="600" \
  -e REFRESH_DURATION="30" \
  -e RANDOM_SELECTION="true" \
  admin9705/radarr-hunter
```

### Docker Compose

For those who prefer Docker Compose, add this to your `docker-compose.yml` file:

```yaml
version: '3'
services:
  radarr-hunter:
    container_name: radarr-hunter
    image: admin9705/radarr-hunter
    restart: always
    environment:
      - API_KEY=your-api-key
      - API_URL=http://radarr:7878
      - MAX_MOVIES=1
      - SLEEP_DURATION=600
      - REFRESH_DURATION=30
      - RANDOM_SELECTION=true
```

Then run:

```bash
docker-compose up -d radarr-hunter
```

To check on the status of the program, you should see new files downloading or you can type:
```bash
docker logs radarr-hunter
```

### Unraid Users

1. Install the plugin called `UserScripts`
2. Copy and paste the following script file as a new script - [radarr-hunter.sh](radarr-hunter.sh) 
3. Ensure to set it to `Run in the background` if your array is already running and set the schedule to `At Startup Array`

<img width="1337" alt="image" src="https://github.com/user-attachments/assets/dbaf9864-1db9-42a5-bd0b-60b6310f9694" />

### SystemD Service

For a more permanent installation on Linux systems using SystemD:

1. Save the script to `/usr/local/bin/radarr-hunter.sh`
2. Make it executable: `chmod +x /usr/local/bin/radarr-hunter.sh`
3. Create a systemd service file at `/etc/systemd/system/radarr-hunter.service`:

```ini
[Unit]
Description=Radarr Hunter Service
After=network.target radarr.service

[Service]
Type=simple
User=your-username
Environment="API_KEY=your-api-key"
Environment="API_URL=http://localhost:7878"
Environment="MAX_MOVIES=1"
Environment="SLEEP_DURATION=600"
Environment="REFRESH_DURATION=30"
Environment="RANDOM_SELECTION=true"
ExecStart=/usr/local/bin/radarr-hunter.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. Enable and start the service:

```bash
sudo systemctl enable radarr-hunter
sudo systemctl start radarr-hunter
```

## Use Cases

- **Library Completion**: Gradually fill in missing movies in your collection
- **New Movie Setup**: Automatically find newly added movies
- **Background Service**: Run it in the background to continuously maintain your library

## Tips

- **First-Time Use**: Start with default settings to ensure it works with your setup
- **Adjusting Speed**: Lower the `SLEEP_DURATION` to search more frequently (be careful with indexer limits)
- **Multiple Movies**: Increase `MAX_MOVIES` if you want to search for more movies per cycle
- **System Resources**: The script uses minimal resources and can run continuously on even low-powered systems

## Troubleshooting

- **API Key Issues**: Check that your API key is correct in Radarr settings
- **Connection Problems**: Ensure the Radarr URL is accessible from where you're running the script
- **Command Failures**: If search commands fail, try using the Radarr UI to verify what commands are available in your version
- **Logs**: Check the container logs with `docker logs radarr-hunter` if running in Docker

---

**Change Log:**
- **v1**: Original code written
- **v2**: Updated variables and code for docker format

---

This script helps automate the tedious process of finding and downloading missing movies in your collection, running quietly in the background while respecting your indexers' rate limits.
