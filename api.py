#!/usr/bin/env python3
"""
Radarr API Helper Functions
Handles all communication with the Radarr API
"""

import requests
import time
import datetime
from typing import List, Dict, Any, Optional, Union
from utils.logger import logger, debug_log
from config import API_KEY, API_URL, API_TIMEOUT, MONITORED_ONLY, SKIP_FUTURE_RELEASES, COMMAND_WAIT_DELAY, COMMAND_WAIT_ATTEMPTS

# Create a session for reuse
session = requests.Session()

def radarr_request(endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Union[Dict, List]]:
    """
    Make a request to the Radarr API (v3).
    `endpoint` should be something like 'movie', 'command', etc.
    """
    url = f"{API_URL}/api/v3/{endpoint}"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = session.get(url, headers=headers, timeout=API_TIMEOUT)
        elif method.upper() == "POST":
            response = session.post(url, headers=headers, json=data, timeout=API_TIMEOUT)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return None

def wait_for_command(command_id: int):
    logger.debug(f"Waiting for command {command_id} to complete...")
    attempts = 0
    while True:
        try:
            time.sleep(COMMAND_WAIT_DELAY)
            response = radarr_request(f"command/{command_id}")
            logger.debug(f"Command {command_id} Status: {response['status']}")
        except Exception as error:
            logger.error(f"Error fetching command status on attempt {attempts + 1}: {error}")
            return False

        attempts += 1

        if response['status'].lower() in ['complete', 'completed'] or attempts >= COMMAND_WAIT_ATTEMPTS:
            break

    if response['status'].lower() not in ['complete', 'completed']:
        logger.warning(f"Command {command_id} did not complete within the allowed attempts.")
        return False

    time.sleep(0.5)

    return response['status'].lower() in ['complete', 'completed']

def get_download_queue_size() -> Optional[int]:
    """
    GET /api/v3/queue
    Returns total number of items in the queue with the status 'downloading'.
    """
    response = radarr_request("queue?status=downloading")
    total_records = response.get("totalRecords", 0)
    if not isinstance(total_records, int):
        total_records = 0
    logger.debug(f"Download Queue Size: {total_records}")

    return total_records

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

def get_missing_movies() -> List[Dict]:
    """
    Get a list of movies that are missing files.
    Filters based on MONITORED_ONLY setting and optionally
    excludes future releases.
    """
    movies = get_movies()
    
    if not movies:
        return []
    
    missing_movies = []
    
    # Get current date in ISO format (YYYY-MM-DD) for date comparison
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    for movie in movies:
        # Skip if not missing a file
        if movie.get('hasFile'):
            continue
            
        # Apply monitored filter if needed
        if MONITORED_ONLY and not movie.get('monitored'):
            continue
            
        # Skip future releases if enabled
        if SKIP_FUTURE_RELEASES:
            # Check physical, digital, and cinema release dates
            physical_release = movie.get('physicalRelease')
            digital_release = movie.get('digitalRelease') 
            in_cinemas = movie.get('inCinemas')
            
            # Use the earliest available release date for comparison
            release_date = None
            if physical_release:
                release_date = physical_release
            elif digital_release:
                release_date = digital_release
            elif in_cinemas:
                release_date = in_cinemas
                
            # Skip if release date exists and is in the future
            if release_date and release_date > current_date:
                logger.debug(f"Skipping future release '{movie.get('title')}' with date {release_date}")
                continue
                
        missing_movies.append(movie)
    
    return missing_movies

def refresh_movie(movie_id: int) -> Optional[Dict]:
    """Refresh a movie by ID"""
    data = {
        "name": "RefreshMovie",
        "movieIds": [movie_id]
    }
    response = radarr_request("command", method="POST", data=data)
    return wait_for_command(response['id'])

def movie_search(movie_id: int) -> Optional[Dict]:
    """Search for a movie by ID"""
    data = {
        "name": "MoviesSearch",
        "movieIds": [movie_id]
    }
    response = radarr_request("command", method="POST", data=data)
    return wait_for_command(response['id'])

def rescan_movie(movie_id: int) -> Optional[Dict]:
    """Rescan movie files"""
    data = {
        "name": "RescanMovie",
        "movieId": movie_id
    }
    response = radarr_request("command", method="POST", data=data)
    return wait_for_command(response['id'])
