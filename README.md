# Huntarr [Radarr Edition] - Force Radarr to Hunt Missing Movies & Upgrade Movie Qualities 

<h2 align="center">Want to Help? Click the Star in the Upper-Right Corner! ⭐</h2>

<table>
  <tr>
    <td colspan="2"><img src="https://github.com/user-attachments/assets/3ea6d2a0-19fd-4e7c-9dfd-797e735b2955" width="100%"/></td>
  </tr>
</table>

**NOTE**: This utilizes Radarr API Version - `3`.

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

This script continually searches your Radarr library for movies with missing files and movies that need quality upgrades. It automatically triggers searches for both missing movies and movies below your quality cutoff. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your movie collection with the best available quality.

## Related Projects

* [Huntarr - Sonarr Edition](https://github.com/plexguide/Huntarr-Sonarr) - Sister version for TV Shows
* [Huntarr - Lidarr Edition](https://github.com/plexguide/Huntarr-Lidarr) - Sister version for Music
* [Huntarr - Readarr Edition](https://github.com/plexguide/Huntarr-Readarr) - Sister version for Books
* [Unraid Intel ARC Deployment](https://github.com/plexguide/Unraid_Intel-ARC_Deployment) - Convert videos to AV1 Format (I've saved 325TB encoding to AV1)
* Visit [PlexGuide](https://plexguide.com) for more great scripts

## PayPal Donations – Building My Daughter's Future

My 12-year-old daughter is passionate about singing, dancing, and exploring STEM. She consistently earns A-B honors and dreams of a bright future. Every donation goes directly into her college fund, helping turn those dreams into reality. Thank you for your generous support!

[![Donate with PayPal button](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate?hosted_button_id=58AYJ68VVMGSC)

## Features

- 🔄 **Continuous Operation**: Runs indefinitely until manually stopped
- 🎯 **Dual Targeting System**: Targets both missing movies and quality upgrades
- 🎲 **Random Selection**: By default, selects movies randomly to distribute searches across your library
- ⏱️ **Throttled Searches**: Includes configurable delays to prevent overloading indexers
- 📊 **Status Reporting**: Provides clear feedback about what it's doing and which movies it's searching for
- 🛡️ **Error Handling**: Gracefully handles connection issues and API failures
- 🔁 **State Tracking**: Remembers which movies have been processed to avoid duplicate searches
- ⚙️ **Configurable Reset Timer**: Automatically resets search history after a configurable period
- 📦 **Modular Design**: Modern codebase with separated concerns for easier maintenance
- ⏲️ **Configurable Timeouts**: Adjustable API timeout for large libraries
- 🗓️ **Future Release Filtering**: Option to skip movies with future release dates

## Indexers Approving of Huntarr:
* https://ninjacentral.co.za

## How It Works

1. **Initialization**: Connects to your Radarr instance and analyzes your library
2. **Missing Movies**: 
   - Identifies movies without files
   - Optionally filters out future releases
   - Randomly selects movies to process (up to configurable limit)
   - Refreshes metadata and triggers searches
3. **Quality Upgrades**:
   - Finds movies that don't meet your quality cutoff settings
   - Processes them in configurable batches
   - Uses smart selection to distribute searches
4. **State Management**:
   - Tracks which movies have been processed
   - Automatically resets this tracking after a configurable time period
5. **Repeat Cycle**: Waits for a configurable period before starting the next cycle

<table>
  <tr>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/24efae78-ddb9-4e5c-9bee-c66c156a1a83" width="100%"/>
      <p align="center"><em>Missing Movies Demo</em></p>
    </td>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/c72c6e37-5bcd-4315-b20e-8922a570babd" width="100%"/>
      <p align="center"><em>Quality Upgrade Demo</em></p>
    </td>
  </tr>
  <tr>
    <td colspan="2">
      <img src="https://github.com/user-attachments/assets/3e95f6d5-4a96-4bb8-a5b9-1d7b871ff94a" width="100%"/>
      <p align="center"><em>State Management System</em></p>
    </td>
  </tr>
</table>

## Configuration Options

The following environment variables can be configured:

| Variable                     | Description                                                              | Default    |
|------------------------------|-----------------------------------------------------------------------|---------------|
| `API_KEY`                    | Your Radarr API key                                                      | Required   |
| `API_URL`                    | URL to your Radarr instance                                              | Required   |
| `API_TIMEOUT`                | Timeout in seconds for API requests to Radarr                            | 60         |
| `MONITORED_ONLY`             | Only process monitored movies                                            | true       |
| `SKIP_FUTURE_RELEASES`       | Skip processing movies with release dates in the future                  | true       |
| `HUNT_MISSING_MOVIES`        | Maximum missing movies to process per cycle                              | 1          |
| `HUNT_UPGRADE_MOVIES`        | Maximum upgrade movies to process per cycle                              | 5          |
| `SLEEP_DURATION`             | Seconds to wait after completing a cycle (900 = 15 minutes)              | 900        |
| `RANDOM_SELECTION`           | Use random selection (`true`) or sequential (`false`)                    | true       |
| `STATE_RESET_INTERVAL_HOURS` | Hours which the processed state files reset (168=1 week, 0=never reset)  | 168        |
| `DEBUG_MODE`                 | Enable detailed debug logging (`true` or `false`)                        | false      |

### Detailed Configuration Explanation

- **API_TIMEOUT**
  - Sets the maximum number of seconds to wait for Radarr API responses before timing out.
  - This is particularly important when working with large libraries.
  - If you experience timeout errors, increase this value.
  - For libraries with thousands of movies, values of 90-120 seconds may be necessary.
  - Default is 60 seconds, which works well for most medium-sized libraries.

- **SKIP_FUTURE_RELEASES**
  - When set to `true`, movies with release dates in the future will be skipped during missing movie processing.
  - This prevents searching for content that isn't yet available.
  - The script checks physical, digital, and theater release dates.
  - Set to `false` if you want to process all missing movies regardless of release date.

- **HUNT_MISSING_MOVIES**  
  - Sets the maximum number of missing movies to process in each cycle.  
  - Once this limit is reached, the script stops processing further missing movies until the next cycle.
  - Set to `0` to disable missing movie processing completely.

- **HUNT_UPGRADE_MOVIES**  
  - Sets the maximum number of upgrade movies to process in each cycle.  
  - When this limit is reached, the upgrade portion of the cycle stops.
  - Set to `0` to disable quality upgrade processing completely.

- **RANDOM_SELECTION**
  - When `true`, selects movies randomly, which helps distribute searches across your library.
  - When `false`, processes movies sequentially, which can be more predictable and methodical.

- **STATE_RESET_INTERVAL_HOURS**  
  - Controls how often the script "forgets" which movies it has already processed.  
  - The script records the IDs of missing movies and upgrade movies that have been processed.  
  - When the age of these records exceeds the number of hours set by this variable, the records are cleared automatically.  
  - This reset allows the script to re-check movies that were previously processed, so if there are changes (such as improved quality), they can be processed again.
  - Setting this to `0` will disable the reset functionality entirely - processed items will be remembered indefinitely.
  - Default is 168 hours (one week) - meaning the script will start fresh weekly.

- **DEBUG_MODE**
  - When set to `true`, the script will output detailed debugging information about API responses and internal operations.
  - Useful for troubleshooting issues but can make logs verbose.

---

## Installation Methods

### Docker Run

The simplest way to run Huntarr is via Docker:

```bash
docker run -d --name huntarr-radarr \
  --restart always \
  -e API_KEY="your-api-key" \
  -e API_URL="http://your-radarr-address:7878" \
  -e API_TIMEOUT="60" \
  -e MONITORED_ONLY="true" \
  -e SKIP_FUTURE_RELEASES="true" \
  -e HUNT_MISSING_MOVIES="1" \
  -e HUNT_UPGRADE_MOVIES="0" \
  -e SLEEP_DURATION="900" \
  -e RANDOM_SELECTION="true" \
  -e STATE_RESET_INTERVAL_HOURS="168" \
  -e DEBUG_MODE="false" \
  huntarr/4radarr:latest

To check on the status of the program, you should see new files downloading or you can type:
```bash
docker logs huntarr-radarr
```

### Docker Compose

For those who prefer Docker Compose, add this to your `docker-compose.yml` file:

```yaml
version: "3.8"
services:
  huntarr-radarr:
    image: huntarr/4radarr:latest
    container_name: huntarr-radarr
    restart: always
    environment:
      API_KEY: "your-api-key"
      API_URL: "http://your-radarr-address:7878"
      API_TIMEOUT: "60"
      MONITORED_ONLY: "true"
      SKIP_FUTURE_RELEASES: "true"
      HUNT_MISSING_MOVIES: "1"
      HUNT_UPGRADE_MOVIES: "0"
      SLEEP_DURATION: "900"
      RANDOM_SELECTION: "true"
      STATE_RESET_INTERVAL_HOURS: "168"
      DEBUG_MODE: "false"
```

Then run:

```bash
docker-compose up -d huntarr-radarr
```

To check on the status of the program, you should see new files downloading or you can type:
```bash
docker logs huntarr-radarr
```

### Unraid Users

Run from the Unraid Command Line. This will eventaully be submitted to the Unraid App Store

```bash
docker run -d --name huntarr-radarr \
  --restart always \
  -e API_KEY="your-api-key" \
  -e API_URL="http://your-radarr-address:7878" \
  -e API_TIMEOUT="60" \
  -e MONITORED_ONLY="true" \
  -e SKIP_FUTURE_RELEASES="true" \
  -e HUNT_MISSING_MOVIES="1" \
  -e HUNT_UPGRADE_MOVIES="0" \
  -e SLEEP_DURATION="900" \
  -e RANDOM_SELECTION="true" \
  -e STATE_RESET_INTERVAL_HOURS="168" \
  -e DEBUG_MODE="false" \
  huntarr/4radarr:latest
```

### SystemD Service

For a more permanent installation on Linux systems using SystemD:

1. Save the script to `/usr/local/bin/huntarr.sh`
2. Make it executable: `chmod +x /usr/local/bin/huntarr.sh`
3. Create a systemd service file at `/etc/systemd/system/huntarr.service`:

```ini
[Unit]
Description=Huntarr Service
After=network.target radarr.service

[Service]
Type=simple
User=your-username
Environment="API_KEY=your-api-key"
Environment="API_URL=http://localhost:7878"
Environment="API_TIMEOUT=60"
Environment="MONITORED_ONLY=true"
Environment="SKIP_FUTURE_RELEASES=true"
Environment="HUNT_MISSING_MOVIES=1"
Environment="HUNT_UPGRADE_MOVIES=0"
Environment="SLEEP_DURATION=900"
Environment="RANDOM_SELECTION=true"
Environment="STATE_RESET_INTERVAL_HOURS=168"
Environment="DEBUG_MODE=false"
ExecStart=/usr/local/bin/huntarr.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. Enable and start the service:

```bash
sudo systemctl enable huntarr
sudo systemctl start huntarr
```

## Use Cases

- **Library Completion**: Gradually fill in missing movies in your collection
- **Quality Improvement**: Automatically upgrade movie quality as better versions become available
- **New Movie Setup**: Automatically find newly added movies
- **Background Service**: Run it in the background to continuously maintain your library
- **Smart Rotation**: With state tracking, ensures all content gets attention over time
- **Large Library Management**: With optimized performance and configurable timeouts, handles even the largest libraries
- **Release Date Awareness**: Skip movies that aren't released yet, focusing only on currently available content

## Tips

- **First-Time Use**: Start with default settings to ensure it works with your setup
- **Adjusting Speed**: Lower the `SLEEP_DURATION` to search more frequently (be careful with indexer limits)
- **Batch Size Control**: Adjust `HUNT_MISSING_MOVIES` and `HUNT_UPGRADE_MOVIES` based on your indexer's rate limits
- **Monitored Status**: Set `MONITORED_ONLY=false` if you want to download all missing movies regardless of monitored status
- **System Resources**: The script uses minimal resources and can run continuously on even low-powered systems
- **Debugging Issues**: Enable `DEBUG_MODE=true` temporarily to see detailed logs when troubleshooting
- **API Timeouts**: If you have a large library, increase the `API_TIMEOUT` value to 90-120 seconds to prevent timeout errors
- **Future Releases**: Use `SKIP_FUTURE_RELEASES=true` to avoid searching for movies not yet released

## Troubleshooting

- **API Key Issues**: Check that your API key is correct in Radarr settings
- **Connection Problems**: Ensure the Radarr URL is accessible from where you're running the script
- **Command Failures**: If search commands fail, try using the Radarr UI to verify what commands are available in your version
- **Logs**: Check the container logs with `docker logs huntarr-radarr` if running in Docker
- **Debug Mode**: Enable `DEBUG_MODE=true` to see detailed API responses and process flow
- **State Files**: The script stores state in `/tmp/huntarr-state/` - if something seems stuck, you can try deleting these files
- **Timeout Errors**: If you see "Read timed out" errors, increase the `API_TIMEOUT` value to give Radarr more time to respond

---

**Change Log:**
- **v1**: Original code written
- **v2**: Added dual targeting for both missing and quality upgrade movies
- **v3**: Added state tracking to prevent duplicate searches
- **v4**: Implemented configurable state reset timer
- **v5**: Added debug mode and improved error handling
- **v6**: Enhanced random selection mode for better distribution
- **v7**: Renamed from "Radarr Hunter" to "Huntarr [Radarr Edition]"
- **v8**: Complete modular refactoring for better maintainability
- **v9**: Added configurable API timeout and standardized parameter naming with HUNT_ prefix
- **v10**: Added version tags for improved stability and predictable updates
- **v11**: Added SKIP_FUTURE_RELEASES option to prevent searching for unreleased movies

---

This script helps automate the tedious process of finding missing movies and quality upgrades in your collection, running quietly in the background while respecting your indexers' rate limits.

---

Thanks to: 

[IntensiveCareCub](https://www.reddit.com/user/IntensiveCareCub/) for the Hunter to Huntarr idea!
