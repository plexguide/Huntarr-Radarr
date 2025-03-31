# Radarr Hunter - Force Radarr to Hunt Missing Movies

<h2 align="center">Want to Help? Click the Star in the Upper-Right Corner! ⭐</h2>

**NOTE**  
This utilizes Radarr API Version - `3`. The Script: [radarr-hunter.sh](radarr-hunter.sh)

To run via Docker (this will be improved later) 

```bash
docker run -d --name radarr-hunter \
  -e API_KEY="your-api-key" \
  -e API_URL="http://your-radarr-address:7878" \
  -e MAX_MOVIES="1" \
  -e SLEEP_DURATION="600" \
  -e REFRESH_DURATION="30" \
  -e RANDOM_SELECTION="true" \
  admin9705/radarr-hunter
```

**Change Log:**
- **v1**: Original code written
- **v2**: Updated variables and code for docker format

<img width="985" alt="image" src="https://github.com/user-attachments/assets/c5f54723-6828-4633-8c9c-54f25f4a1e9c" />


### Other Project Guide (Just FYI)

* Sister Version (Sonarr): https://github.com/plexguide/Sonarr-Hunter<br>
* Visit: https://github.com/plexguide/Unraid_Intel-ARC_Deployment - Converts videos to AV1 Format (I've saved 325TB encoding to AV1)
* For other scripts great scripts, visit https://plexguide.com

# Radarr Missing Movie Search Tool

## Overview

This script continually searches your Radarr library specifically for movies that are missing (monitored but not downloaded) and automatically triggers searches for those missing movies. It's designed to run continuously while being gentle on your indexers, helping you gradually complete your movie collection.

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

At the top of the script, you'll find these configurable options:

```bash
API_KEY="your_api_key_here"            # Your Radarr API key
RADARR_URL="http://your.radarr.ip:port" # URL to your Radarr instance
MAX_MOVIES=1                            # Movies to process before restarting cycle
SLEEP_DURATION=600                      # Seconds to wait after processing a movie (300=5min)
REFRESH_DURATION="30"                   # This is a pause between multiple movies if MAX_MOVIES > 1 (a mini sleep)
RANDOM_SELECTION=true                   # true for random selection, false for sequential
```

## Use Cases

- **Library Completion**: Gradually fill in missing movies in your collection
- **New Movie Setup**: Automatically find newly added movies
- **Background Service**: Run it in the background to continuously maintain your library

## How to Run (Unraid Users)

1. Install the plugin called `UserScripts`
2. Copy and paste the following script file as new script - [radarr-hunter.sh](radarr-hunter.sh) 
3. Ensure to set it to `Run in the background` if your array is already running and set the schedule to `At Startup Array`

<img width="1337" alt="image" src="https://github.com/user-attachments/assets/dbaf9864-1db9-42a5-bd0b-60b6310f9694" />

## How to Run (Non-Unraid Users)

1. Save the script to a file (e.g., `radarr-hunter.sh`)
2. Make it executable: `chmod +x radarr-hunter.sh`
3. Run it: `./radarr-hunter.sh`

For continuous background operation:
- Use `screen` or `tmux`: `screen -S radarr-hunter ./radarr-hunter.sh`
- Or create a systemd service to run it automatically on startup

## Tips

- **First-Time Use**: Start with default settings to ensure it works with your setup
- **Adjusting Speed**: Lower the `SLEEP_DURATION` to search more frequently (be careful with indexer limits)
- **Multiple Movies**: Increase `MAX_MOVIES` if you want to search for more movies per cycle
- **System Resources**: The script uses minimal resources and can run continuously on even low-powered systems

## Troubleshooting

- **API Key Issues**: Check that your API key is correct in Radarr settings
- **Connection Problems**: Ensure the Radarr URL is accessible from where you're running the script
- **Command Failures**: If search commands fail, try using the Radarr UI to verify what commands are available in your version

---

This script helps automate the tedious process of finding and downloading missing movies in your collection, running quietly in the background while respecting your indexers' rate limits.
