#!/usr/bin/env python3
"""
Quality Upgrade Processing
Handles searching for movies that need quality upgrades in Radarr
"""

import random
import time
from utils.logger import logger
from config import HUNT_UPGRADE_MOVIES, RANDOM_SELECTION
from api import get_cutoff_unmet, refresh_movie, movie_search, rescan_movie
from state import load_processed_ids, save_processed_id, truncate_processed_list, PROCESSED_UPGRADE_FILE

def process_cutoff_upgrades() -> bool:
    """
    Process movies that need quality upgrades.
    
    Returns:
        True if any processing was done, False otherwise
    """
    logger.info("=== Checking for Quality Upgrades (Cutoff Unmet) ===")
    
    # Skip if HUNT_UPGRADE_MOVIES is set to 0
    if HUNT_UPGRADE_MOVIES <= 0:
        logger.info("HUNT_UPGRADE_MOVIES is set to 0, skipping quality upgrades")
        return False
    
    upgrade_movies = get_cutoff_unmet()
    
    if not upgrade_movies:
        logger.info("No movies found that need quality upgrades.")
        return False
    
    logger.info(f"Found {len(upgrade_movies)} movies that need quality upgrades.")
    processed_upgrade_ids = load_processed_ids(PROCESSED_UPGRADE_FILE)
    movies_processed = 0
    processing_done = False
    
    # Randomize or use sequential indices
    indices = list(range(len(upgrade_movies)))
    if RANDOM_SELECTION:
        random.shuffle(indices)
    
    for i in indices:
        if movies_processed >= HUNT_UPGRADE_MOVIES:
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
        if not refresh_res:
            logger.warning("WARNING: Refresh command failed. Skipping this movie.")
            continue
        
        logger.info(f"Refresh command completed successfully.")
        
        # Search
        logger.info(" - Searching for quality upgrade...")
        search_res = movie_search(movie_id)
        if search_res:
            logger.info(f"Search command completed successfully.")
            processing_done = True
            
            # Rescan
            logger.info(" - Rescanning movie folder...")
            rescan_res = rescan_movie(movie_id)
            if rescan_res:
                logger.info(f"Rescan command completed successfully.")
            else:
                logger.warning("WARNING: Rescan command not available or failed.")
            
            # Mark processed
            save_processed_id(PROCESSED_UPGRADE_FILE, movie_id)
            movies_processed += 1
            logger.info(f"Processed {movies_processed}/{HUNT_UPGRADE_MOVIES} upgrade movies this cycle.")
        else:
            logger.warning(f"WARNING: Search command failed for movie ID {movie_id}.")
    
    logger.info(f"Completed processing {movies_processed} upgrade movies for this cycle.")
    truncate_processed_list(PROCESSED_UPGRADE_FILE)
    
    return processing_done