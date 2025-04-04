#!/usr/bin/env python3
"""
Huntarr [Radarr Edition] 
Automatically search for missing movies and quality upgrades in Radarr
"""

import os
import time
import json
import random
import logging
import requests
import pathlib

from typing import List, Dict, Any, Optional, Union

# ---------------------------
# Main Configuration Variables
# ---------------------------

API_KEY = os.environ.get("API_KEY", "your-api-key")
API_URL = os.environ.get("API_URL", "your-ip-address:7878")

# Maximum number of missing movies to process per cycle
try:
    MAX_MISSING = int(os.environ.get("MAX_MISSING", "1"))
except ValueError:
    MAX_MISSING = 1
    print(f"Warning: Invalid MAX_MISSING value, using default: {MAX_MISSING}")

# Maximum number of upgrade movies to process per cycle
try:
    MAX_UPGRADES = int(os.environ.get("MAX_UPGRADES", "5"))
except ValueError:
    MAX_UPGRADES = 5
    print(f"Warning: Invalid MAX_UPGRADES value, using default: {MAX_UPGRADES}")

# Sleep duration in seconds after completing one full cycle (default 15 minutes)
try:
    SLEEP_DURATION = int(os.environ.get("SLEEP_DURATION", "900"))
except ValueError:
    SLEEP_DURATION = 900
    print(f"Warning: Invalid SLEEP_DURATION value, using default: {SLEEP_DURATION}")

# Reset processed state file after this many hours (default 168 hours = 1 week)
try:
    STATE_RESET_INTERVAL_HOURS = int(os.environ.get("STATE_RESET_INTERVAL_HOURS", "168"))
except ValueError:
    STATE_RESET_INTERVAL_HOURS = 168
    print(f"Warning: Invalid STATE_RESET_INTERVAL_HOURS value, using default: {STATE_RESET_INTERVAL_HOURS}")

# ---------------------------
# Miscellaneous Configuration
# ---------------------------

# If True, pick items randomly, if False go in order
RANDOM_SELECTION = os.environ.get("RANDOM_SELECTION", "true").lower() == "true"

# If MONITORED_ONLY is "true", only process missing or upgrade movies from monitored movies
MONITORED_ONLY = os.environ.get("MONITORED_ONLY", "true").lower() == "true"

# SEARCH_TYPE controls what we search for:
# - "missing" => Only find movies that are missing
# - "upgrade" => Only find movies that don't meet quality cutoff
# - "both"    => Do missing movies first, then upgrade movies
SEARCH_TYPE = os.environ.get("SEARCH_TYPE", "both")

# Enable debug mode to see API responses
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("huntarr")

# ---------------------------
# State Tracking Setup
# ---------------------------
STATE_DIR = pathlib.Path("/tmp/huntarr-radarr-state")
STATE_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_MISSING_FILE = STATE_DIR / "processed_missing_ids.txt"
PROCESSED_UPGRADE_FILE = STATE_DIR / "processed_upgrade_ids.txt"

# Create files if they don't exist
PROCESSED_MISSING_FILE.touch(exist_ok=True)
PROCESSED_UPGRADE_FILE.touch(exist_ok=True)

# ---------------------------
# Helper Functions
# ---------------------------
def debug_log(message: str, data: Any = None) -> None:
    """Log debug messages with optional data"""
    if DEBUG_MODE:
        logger.debug(f"{message}")
        if data is not None:
            try:
                as_json = json.dumps(data)
                if len(as_json) > 500:
                    as_json = as_json[:500] + "..."
                logger.debug(as_json)
            except:
                data_str = str(data)
                if len(data_str) > 500:
                    data_str = data_str[:500] + "..."
                logger.debug(data_str)

def load_processed_ids(file_path: pathlib.Path) -> List[int]:
    """Load processed movie IDs from a file"""
    try:
        with open(file_path, 'r') as f:
            return [int(line.strip()) for line in f if line.strip().isdigit()]
    except Exception as e:
        logger.error(f"Error reading processed IDs from {file_path}: {e}")
        return []

def save_processed_id(file_path: pathlib.Path, movie_id: int) -> None:
    """Save a processed movie ID to a file"""
    try:
        with open(file_path, 'a') as f:
            f.write(f"{movie_id}\n")
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")

def truncate_processed_list(file_path: pathlib.Path, max_lines: int = 500) -> None:
    """Truncate the processed list to prevent unbounded growth"""
    try:
        # Only check if file is actually large; you can adjust thresholds if desired
        if file_path.stat().st_size > 10000:  
            lines = file_path.read_text().splitlines()
            if len(lines) > max_lines:
                logger.info(f"Processed list is large. Truncating to last {max_lines} entries.")
                with open(file_path, 'w') as f:
                    f.write('\n'.join(lines[-max_lines:]) + '\n')
    except Exception as e:
        logger.error(f"Error truncating {file_path}: {e}")

def check_state_reset() -> None:
    """Check if state files need to be reset based on their age"""
    if STATE_RESET_INTERVAL_HOURS <= 0:
        logger.info("State reset is disabled. Processed items will be remembered indefinitely.")
        return
    
    missing_age = time.time() - PROCESSED_MISSING_FILE.stat().st_mtime
    upgrade_age = time.time() - PROCESSED_UPGRADE_FILE.stat().st_mtime
    reset_interval_seconds = STATE_RESET_INTERVAL_HOURS * 3600
    
    if missing_age >= reset_interval_seconds or upgrade_age >= reset_interval_seconds:
        logger.info(f"Resetting processed state files (older than {STATE_RESET_INTERVAL_HOURS} hours).")
        PROCESSED_MISSING_FILE.write_text("")
        PROCESSED_UPGRADE_FILE.write_text("")

# ---------------------------
# Radarr API Functions
# ---------------------------
def radarr_request(endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Union[Dict, List]]:
    """Make a request to the Radarr API"""
    url = f"{API_URL}/api/v3/{endpoint}"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return None

def get_movies() -> List[Dict]:
    """Get all movies from Radarr (full list)"""
    result = radarr_request("movie")
    if result:
        debug_log("Raw movies API response sample:", result[:2] if len(result) > 2 else result)
    return result or []

def get_cutoff_unmet() -> List[Dict]:
    """
    Directly query Radarr for only those movies where the quality cutoff is not met.
    This is the most reliable way for big libraries. Optionally filter by monitored.
    """
    query = "movie?qualityCutoffNotMet=true"
    if MONITORED_ONLY:
        # Append &monitored=true to the querystring
        query += "&monitored=true"
    
    # Perform the request
    result = radarr_request(query, method="GET")
    return result or []

def refresh_movie(movie_id: int) -> Optional[Dict]:
    data = {
        "name": "RefreshMovie",
        "movieIds": [movie_id]
    }
    return radarr_request("command", method="POST", data=data)

def movie_search(movie_id: int) -> Optional[Dict]:
    """Search for a movie by ID"""
    data = {
        "name": "MoviesSearch",
        "movieIds": [movie_id]
    }
    return radarr_request("command", method="POST", data=data)

def rescan_movie(movie_id: int) -> Optional[Dict]:
    """Rescan movie files"""
    data = {
        "name": "RescanMovie",
        "movieIds": [movie_id]
    }
    return radarr_request("command", method="POST", data=data)

# ---------------------------
# Missing Movies Logic
# ---------------------------
def process_missing_movies() -> None:
    """Process missing movies from the library"""
    logger.info("=== Checking for Missing Movies ===")
    
    movies = get_movies()
    if not movies:
        logger.error("ERROR: Unable to retrieve movie data from Radarr. Retrying in 60s...")
        time.sleep(60)
        return
    
    if MONITORED_ONLY:
        logger.info("MONITORED_ONLY=true => only monitored movies without files.")
        missing_movies = [m for m in movies if m.get('monitored') and not m.get('hasFile')]
    else:
        logger.info("MONITORED_ONLY=false => all movies without files.")
        missing_movies = [m for m in movies if not m.get('hasFile')]
    
    if not missing_movies:
        logger.info("No missing movies found.")
        return
    
    logger.info(f"Found {len(missing_movies)} movie(s) with missing files.")
    processed_missing_ids = load_processed_ids(PROCESSED_MISSING_FILE)
    movies_processed = 0
    
    indices = list(range(len(missing_movies)))
    if RANDOM_SELECTION:
        random.shuffle(indices)
    
    for i in indices:
        if MAX_MISSING > 0 and movies_processed >= MAX_MISSING:
            break
        
        movie = missing_movies[i]
        movie_id = movie.get('id')
        if not movie_id or movie_id in processed_missing_ids:
            continue
        
        title = movie.get('title', 'Unknown Title')
        year = movie.get('year', 'Unknown Year')
        
        logger.info(f"Processing missing movie \"{title} ({year})\" (ID: {movie_id}).")
        
        # Refresh
        logger.info(" - Refreshing movie...")
        refresh_res = refresh_movie(movie_id)
        if not refresh_res or 'id' not in refresh_res:
            logger.warning(f"WARNING: Refresh command failed for {title}. Skipping.")
            time.sleep(10)
            continue
        
        logger.info(f"Refresh command accepted (ID: {refresh_res.get('id')}). Waiting 5s...")
        time.sleep(5)
        
        # Search
        logger.info(f" - Searching for \"{title}\"...")
        search_res = movie_search(movie_id)
        if search_res and 'id' in search_res:
            logger.info(f"Search command accepted (ID: {search_res.get('id')}).")
        else:
            logger.warning("WARNING: Movie search failed.")
        
        # Rescan
        logger.info(" - Rescanning movie folder...")
        rescan_res = rescan_movie(movie_id)
        if rescan_res and 'id' in rescan_res:
            logger.info(f"Rescan command accepted (ID: {rescan_res.get('id')}).")
        else:
            logger.warning("WARNING: Rescan command not available or failed.")
        
        # Mark processed
        save_processed_id(PROCESSED_MISSING_FILE, movie_id)
        movies_processed += 1
        logger.info(f"Processed {movies_processed}/{MAX_MISSING} missing movies this cycle.")
    
    # Truncate processed list if needed
    truncate_processed_list(PROCESSED_MISSING_FILE)

# ---------------------------
# Quality Upgrades Logic
# ---------------------------
def process_cutoff_upgrades() -> None:
    """Process movies that need quality upgrades."""
    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")
    
    # Instead of retrieving the full movie list and filtering, 
    # directly query the subset of movies that do not meet cutoff:
    upgrade_movies = get_cutoff_unmet()
    
    if not upgrade_movies:
        logger.info("No movies found that need quality upgrades.")
        return
    
    logger.info(f"Found {len(upgrade_movies)} movies that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    movies_processed = 0
    
    indices = list(range(len(upgrade_movies)))
    if RANDOM_SELECTION:
        random.shuffle(indices)
    
    for i in indices:
        if MAX_UPGRADES > 0 and movies_processed >= MAX_UPGRADES:
            break
        
        movie = upgrade_movies[i]
        movie_id = movie.get('id')
        if not movie_id or movie_id in processed_upgrade_ids:
            continue
        
        title = movie.get('title', 'Unknown Title')
        year = movie.get('year', 'Unknown Year')
        logger.info(f"Processing quality upgrade for \"{title} ({year})\" (ID: {movie_id})")
        
        # Refresh
        logger.info(" - Refreshing movie information...")
        refresh_res = refresh_movie(movie_id)
        if not refresh_res or 'id' not in refresh_res:
            logger.warning("WARNING: Refresh command failed. Skipping this movie.")
            time.sleep(10)
            continue
        
        logger.info(f"Refresh command accepted (ID: {refresh_res.get('id')}). Waiting 5s...")
        time.sleep(5)
        
        # Search
        logger.info(" - Searching for quality upgrade...")
        search_res = movie_search(movie_id)
        if search_res and 'id' in search_res:
            logger.info(f"Search command accepted (ID: {search_res.get('id')}).")
            
            # Rescan
            logger.info(" - Rescanning movie folder...")
            rescan_res = rescan_movie(movie_id)
            if rescan_res and 'id' in rescan_res:
                logger.info(f"Rescan command accepted (ID: {rescan_res.get('id')}).")
            else:
                logger.warning("WARNING: Rescan command not available or failed.")
            
            # Mark processed
            save_processed_id(PROCESSED_UPGRADE_FILE, movie_id)
            movies_processed += 1
            logger.info(f"Processed {movies_processed}/{MAX_UPGRADES} upgrade movies this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for movie ID {movie_id}.")
            time.sleep(10)
    
    logger.info(f"Completed processing {movies_processed} upgrade movies for this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)

# ---------------------------
# Main Loop
# ---------------------------
def calculate_reset_time() -> None:
    """Calculate and display time until the next state reset."""
    if STATE_RESET_INTERVAL_HOURS <= 0:
        logger.info("State reset is disabled. Processed items will be remembered indefinitely.")
        return
    
    current_time = time.time()
    missing_age = current_time - PROCESSED_MISSING_FILE.stat().st_mtime
    upgrade_age = current_time - PROCESSED_UPGRADE_FILE.stat().st_mtime
    
    reset_interval_seconds = STATE_RESET_INTERVAL_HOURS * 3600
    missing_remaining = reset_interval_seconds - missing_age
    upgrade_remaining = reset_interval_seconds - upgrade_age
    
    remaining_seconds = min(missing_remaining, upgrade_remaining)
    remaining_minutes = int(remaining_seconds / 60)
    
    logger.info(f"State reset will occur in approximately {remaining_minutes} minutes.")

def main_loop() -> None:
    """Main processing loop"""
    while True:
        # Reset old state files if needed
        check_state_reset()
        
        # Process based on SEARCH_TYPE
        if SEARCH_TYPE == "missing":
            process_missing_movies()
        elif SEARCH_TYPE == "upgrade":
            process_cutoff_upgrades()
        elif SEARCH_TYPE == "both":
            process_missing_movies()
            process_cutoff_upgrades()
        else:
            logger.error(f"Unknown SEARCH_TYPE={SEARCH_TYPE}. Use 'missing','upgrade','both'.")
        
        # Calculate minutes remaining until state reset
        calculate_reset_time()
        
        logger.info(f"Cycle complete. Waiting {SLEEP_DURATION} seconds before next cycle...")
        logger.info("⭐ Enjoy the Tool? Donate @ https://donate.plex.one towards my Daughter's 501 College Fund!")
        time.sleep(SLEEP_DURATION)

if __name__ == "__main__":
    logger.info("=== Huntarr [Radarr Edition] Starting ===")
    logger.info(f"API URL: {API_URL}")
    debug_log(f"API KEY: {API_KEY}")
    logger.info(f"Configuration: MAX_MISSING={MAX_MISSING}, MAX_UPGRADES={MAX_UPGRADES}, SLEEP_DURATION={SLEEP_DURATION}s")
    logger.info(f"Configuration: MONITORED_ONLY={MONITORED_ONLY}, RANDOM_SELECTION={RANDOM_SELECTION}, SEARCH_TYPE={SEARCH_TYPE}")
    
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Huntarr stopped by user.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
