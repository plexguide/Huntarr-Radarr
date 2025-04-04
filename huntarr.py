#!/usr/bin/env python3
"""
Huntarr [Radarr Edition] - Python Version
Automatically search for missing movies and quality upgrades in Radarr
"""

import os
import time
import json
import random
import logging
import requests
import datetime
import pathlib
from typing import List, Dict, Any, Optional, Union

# ---------------------------
# Main Configuration Variables
# ---------------------------

API_KEY = os.environ.get("API_KEY", "your-api-key")
API_URL = os.environ.get("API_URL", "http://your-radarr-address:7878")

# Maximum number of missing movies to process per cycle
MAX_MISSING = int(os.environ.get("MAX_MISSING", "1"))

# Maximum number of upgrade movies to process per cycle
MAX_UPGRADES = int(os.environ.get("MAX_UPGRADES", "5"))

# Sleep duration in seconds after completing one full cycle (default 15 minutes)
SLEEP_DURATION = int(os.environ.get("SLEEP_DURATION", "900"))

# Reset processed state file after this many hours (default 168 hours = 1 week)
STATE_RESET_INTERVAL_HOURS = int(os.environ.get("STATE_RESET_INTERVAL_HOURS", "168"))

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
            if isinstance(data, (dict, list)):
                try:
                    logger.debug(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
                except:
                    logger.debug(str(data)[:500] + "..." if len(str(data)) > 500 else str(data))
            else:
                logger.debug(str(data)[:500] + "..." if len(str(data)) > 500 else str(data))

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
        if file_path.stat().st_size > 10000:  # Only check if file is getting large
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
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
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
    """Get all movies from Radarr"""
    result = radarr_request("movie")
    debug_log("Raw movies API response sample:", result[:2] if result and len(result) > 2 else result)
    return result or []

def refresh_movie(movie_id: int) -> Optional[Dict]:
    """Refresh movie metadata"""
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
    
    # Get all movies
    movies = get_movies()
    if not movies:
        logger.error("ERROR: Unable to retrieve movie data from Radarr. Retrying in 60s...")
        time.sleep(60)
        return
    
    # Filter for missing movies
    if MONITORED_ONLY:
        logger.info("MONITORED_ONLY=true => only monitored movies without files.")
        missing_movies = [m for m in movies if m.get('monitored', False) and not m.get('hasFile', False)]
    else:
        logger.info("MONITORED_ONLY=false => all movies without files.")
        missing_movies = [m for m in movies if not m.get('hasFile', False)]
    
    debug_log(f"Total missing movies: {len(missing_movies)}")
    if len(missing_movies) > 0:
        debug_log("First missing movie (if any):", missing_movies[0] if missing_movies else None)
    
    if not missing_movies:
        logger.info("No missing movies found.")
        return
    
    # Load list of already processed movie IDs
    processed_missing_ids = load_processed_ids(PROCESSED_MISSING_FILE)
    
    logger.info(f"Found {len(missing_movies)} movie(s) with missing files.")
    movies_processed = 0
    
    # Process movies in random or sequential order
    indices = list(range(len(missing_movies)))
    if RANDOM_SELECTION:
        random.shuffle(indices)
    
    for index in indices:
        if MAX_MISSING > 0 and movies_processed >= MAX_MISSING:
            break
        
        movie = missing_movies[index]
        movie_id = movie.get('id')
        
        # Skip if already processed in past cycles
        if movie_id in processed_missing_ids:
            continue
        
        movie_title = movie.get('title', 'Unknown Title')
        movie_year = movie.get('year', 'Unknown Year')
        
        logger.info(f"Processing missing movie \"{movie_title} ({movie_year})\" (ID: {movie_id}).")
        
        # Step 1: Refresh movie metadata
        logger.info(" - Refreshing movie...")
        refresh_result = refresh_movie(movie_id)
        if not refresh_result or 'id' not in refresh_result:
            logger.warning(f"WARNING: Refresh command failed for {movie_title}. Skipping.")
            time.sleep(10)
            continue
        
        refresh_id = refresh_result.get('id')
        logger.info(f"Refresh command accepted (ID: {refresh_id}). Waiting 5s...")
        time.sleep(5)
        
        # Step 2: Search for the movie
        logger.info(f" - Searching for \"{movie_title}\"...")
        search_result = movie_search(movie_id)
        if search_result and 'id' in search_result:
            search_id = search_result.get('id')
            logger.info(f"Search command accepted (ID: {search_id}).")
        else:
            logger.warning("WARNING: Movie search failed.")
        
        # Step 3: Rescan movie folder
        logger.info(" - Rescanning movie folder...")
        rescan_result = rescan_movie(movie_id)
        if rescan_result and 'id' in rescan_result:
            rescan_id = rescan_result.get('id')
            logger.info(f"Rescan command accepted (ID: {rescan_id}).")
        else:
            logger.warning("WARNING: Rescan command not available or failed.")
        
        # Mark as processed and increment counter
        save_processed_id(PROCESSED_MISSING_FILE, movie_id)
        movies_processed += 1
        logger.info(f"Processed {movies_processed}/{MAX_MISSING} missing movies this cycle.")
    
    # Truncate processed list if needed
    truncate_processed_list(PROCESSED_MISSING_FILE)

# ---------------------------
# Quality Upgrades Logic
# ---------------------------
def process_cutoff_upgrades() -> None:
    """Process movies that need quality upgrades"""
    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")
    
    # Get all movies
    movies = get_movies()
    if not movies:
        logger.error("ERROR: Unable to retrieve movie data from Radarr. Retrying in 60s...")
        time.sleep(60)
        return
    
    # Filter for movies that need quality upgrades
    if MONITORED_ONLY:
        logger.info("MONITORED_ONLY=true => only monitored movies needing quality upgrades.")
        upgrade_movies = [m for m in movies if m.get('monitored', False) and 
                         m.get('hasFile', False) and 
                         m.get('qualityCutoffNotMet', False)]
    else:
        logger.info("MONITORED_ONLY=false => all movies needing quality upgrades.")
        upgrade_movies = [m for m in movies if m.get('hasFile', False) and 
                         m.get('qualityCutoffNotMet', False)]
    
    debug_log(f"Found {len(upgrade_movies)} movies that need quality upgrades")
    if len(upgrade_movies) > 0:
        debug_log("First upgrade movie (if any):", upgrade_movies[0] if upgrade_movies else None)
    
    if not upgrade_movies:
        logger.info("No movies found that need quality upgrades.")
        return
    
    # Load list of already processed movie IDs
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    
    logger.info(f"Found {len(upgrade_movies)} movies that need quality upgrades.")
    movies_processed = 0
    
    # Process movies in random or sequential order
    indices = list(range(len(upgrade_movies)))
    if RANDOM_SELECTION:
        random.shuffle(indices)
    
    for index in indices:
        if MAX_UPGRADES > 0 and movies_processed >= MAX_UPGRADES:
            break
        
        movie = upgrade_movies[index]
        movie_id = movie.get('id')
        
        # Skip if already processed in past cycles
        if movie_id in processed_upgrade_ids:
            continue
        
        movie_title = movie.get('title', 'Unknown Title')
        movie_year = movie.get('year', 'Unknown Year')
        
        logger.info(f"Processing quality upgrade for \"{movie_title} ({movie_year})\" (ID: {movie_id})")
        
        # Step 1: Refresh movie metadata
        logger.info(" - Refreshing movie information...")
        refresh_result = refresh_movie(movie_id)
        if not refresh_result or 'id' not in refresh_result:
            logger.warning(f"WARNING: Refresh command failed. Skipping this movie.")
            time.sleep(10)
            continue
        
        refresh_id = refresh_result.get('id')
        logger.info(f"Refresh command accepted (ID: {refresh_id}). Waiting 5s...")
        time.sleep(5)
        
        # Step 2: Search for quality upgrade
        logger.info(" - Searching for quality upgrade...")
        search_result = movie_search(movie_id)
        if search_result and 'id' in search_result:
            search_id = search_result.get('id')
            logger.info(f"Search command accepted (ID: {search_id}).")
            
            # Step 3: Rescan movie folder
            logger.info(" - Rescanning movie folder...")
            rescan_result = rescan_movie(movie_id)
            if rescan_result and 'id' in rescan_result:
                rescan_id = rescan_result.get('id')
                logger.info(f"Rescan command accepted (ID: {rescan_id}).")
            else:
                logger.warning("WARNING: Rescan command not available or failed.")
            
            # Mark as processed and increment counter
            save_processed_id(PROCESSED_UPGRADE_FILE, movie_id)
            movies_processed += 1
            logger.info(f"Processed {movies_processed}/{MAX_UPGRADES} upgrade movies this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for movie ID {movie_id}.")
            time.sleep(10)
    
    logger.info(f"Completed processing {movies_processed} upgrade movies for this cycle.")
    
    # Truncate processed list if needed
    truncate_processed_list(PROCESSED_UPGRADE_FILE)

# ---------------------------
# Main Loop
# ---------------------------
def calculate_reset_time() -> None:
    """Calculate and display time until the next state reset"""
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
        # Check if state files need to be reset
        check_state_reset()
        
        # Process movies based on search type
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