#!/usr/bin/env python3
"""
Missing Movie Processing
Handles searching for missing movies in Radarr
"""

import random
import time
from typing import List
from utils.logger import logger
from config import HUNT_MISSING_MOVIES, MONITORED_ONLY, RANDOM_SELECTION
from api import get_missing_movies, refresh_movie, movie_search, rescan_movie
from state import load_processed_ids, save_processed_id, truncate_processed_list, PROCESSED_MISSING_FILE

def process_missing_movies() -> bool:
    """
    Process movies that are missing files.
    
    Returns:
        True if any processing was done, False otherwise
    """
    logger.info("=== Checking for Missing Movies ===")

    # Skip if HUNT_MISSING_MOVIES is set to 0
    if HUNT_MISSING_MOVIES <= 0:
        logger.info("HUNT_MISSING_MOVIES is set to 0, skipping missing content")
        return False

    missing_movies = get_missing_movies()
    if not missing_movies:
        logger.info("No missing movies found.")
        return False
    
    logger.info(f"Found {len(missing_movies)} movie(s) with missing files.")
    processed_missing_ids = load_processed_ids(PROCESSED_MISSING_FILE)
    movies_processed = 0
    processing_done = False
    
    # Randomize or use sequential indices
    indices = list(range(len(missing_movies)))
    if RANDOM_SELECTION:
        random.shuffle(indices)
    
    for i in indices:
        if movies_processed >= HUNT_MISSING_MOVIES:
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
        if not refresh_res:
            logger.warning(f"WARNING: Refresh command failed for {title}. Skipping.")
            continue
        
        # Search
        logger.info(f" - Searching for \"{title}\"...")
        search_res = movie_search(movie_id)
        if search_res:
            logger.info(f"Search command completed successfully.")
            processing_done = True
        else:
            logger.warning("WARNING: Movie search failed.")
            continue
        
        # Rescan
        logger.info(" - Rescanning movie folder...")
        rescan_res = rescan_movie(movie_id)
        if rescan_res:
            logger.info(f"Rescan command completed successfully.")
        else:
            logger.warning("WARNING: Rescan command not available or failed.")
        
        # Mark processed
        save_processed_id(PROCESSED_MISSING_FILE, movie_id)
        movies_processed += 1
        logger.info(f"Processed {movies_processed}/{HUNT_MISSING_MOVIES} missing movies this cycle.")
    
    # Truncate processed list if needed
    truncate_processed_list(PROCESSED_MISSING_FILE)
    
    return processing_done