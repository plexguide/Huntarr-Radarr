#!/usr/bin/env bash
# ---------------------------
# Configuration
# ---------------------------
API_KEY="fff4318f18ca48da8fb33a9fe5b136c2"
RADARR_URL="http://10.0.0.10:7878"
# How many movies to process before restarting the search cycle
MAX_MOVIES=1
# Sleep duration in seconds after finding a movie with missing file (300=5min)
SLEEP_DURATION=300
# Sleep duration after just refreshing a movie (shorter wait)
REFRESH_DURATION=30
# Set to true to pick movies randomly, false to go in order
RANDOM_SELECTION=true

# ---------------------------
# Main infinite loop
# ---------------------------
while true; do
  # ---------------------------
  # Fetch only missing movies from Radarr
  # ---------------------------
  echo "Retrieving missing movies from Radarr..."
  # Filter to only get monitored movies without files
  MISSING_MOVIES_JSON=$(curl -s \
    -H "X-Api-Key: $API_KEY" \
    "$RADARR_URL/api/v3/movie" | \
    jq '[.[] | select(.monitored==true and .hasFile==false)]')

  # If the above command fails or returns nothing, wait and retry
  if [ -z "$MISSING_MOVIES_JSON" ]; then
    echo "ERROR: Unable to retrieve movie data from Radarr. Retrying in 60 seconds..."
    sleep 60
    continue
  fi

  # Count how many missing movies are in the list
  TOTAL_MISSING=$(echo "$MISSING_MOVIES_JSON" | jq 'length')
  if [ "$TOTAL_MISSING" -eq 0 ]; then
    echo "No missing movies found in Radarr. Waiting 60 seconds before checking again..."
    sleep 60
    continue
  fi
  echo "Found $TOTAL_MISSING missing movie(s)."

  # ---------------------------
  # Process missing movies based on configuration
  # ---------------------------
  echo "Using ${RANDOM_SELECTION:+random}${RANDOM_SELECTION:-sequential} selection."
  echo "Will process up to ${MAX_MOVIES:-all} movies with full refresh."

  MOVIES_PROCESSED=0
  ALREADY_CHECKED=()

  while true; do
    # Check if we've reached the maximum number of movies to process
    if [ "$MAX_MOVIES" -gt 0 ] && [ "$MOVIES_PROCESSED" -ge "$MAX_MOVIES" ]; then
      echo "Reached maximum number of movies to process ($MAX_MOVIES). Restarting search cycle..."
      break
    fi

    # Check if we've checked all missing movies
    if [ ${#ALREADY_CHECKED[@]} -eq "$TOTAL_MISSING" ] || [ "$TOTAL_MISSING" -eq 0 ]; then
      echo "All missing movies have been checked. Waiting before starting a new cycle..."
      sleep 60
      break
    fi

    # Select next movie index based on selection method
    if [ "$RANDOM_SELECTION" = true ] && [ "$TOTAL_MISSING" -gt 1 ]; then
      # Keep generating random indices until we find one we haven't checked yet
      while true; do
        INDEX=$((RANDOM % TOTAL_MISSING))
        # Check if this index has already been processed
        if [[ ! " ${ALREADY_CHECKED[*]} " =~ " ${INDEX} " ]]; then
          break
        fi
      done
    else
      # Find the first index that hasn't been checked yet
      for ((i=0; i<TOTAL_MISSING; i++)); do
        if [[ ! " ${ALREADY_CHECKED[*]} " =~ " ${i} " ]]; then
          INDEX=$i
          break
        fi
      done
    fi

    # Add this index to the list of checked indices
    ALREADY_CHECKED+=("$INDEX")

    # Extract movie information
    MOVIE=$(echo "$MISSING_MOVIES_JSON" | jq ".[$INDEX]")
    MOVIE_ID=$(echo "$MOVIE" | jq '.id')
    MOVIE_TITLE=$(echo "$MOVIE" | jq -r '.title')
    MOVIE_YEAR=$(echo "$MOVIE" | jq -r '.year')
    
    echo "Selected missing movie \"$MOVIE_TITLE ($MOVIE_YEAR)\"..."
    
    # ---------------------------
    # Perform commands to try to get the movie to download
    # ---------------------------
    
    # Step 1: Refresh the movie to make sure Radarr has latest information
    echo "1. Refreshing movie information for \"$MOVIE_TITLE ($MOVIE_YEAR)\" (ID: $MOVIE_ID)..."
    REFRESH_COMMAND=$(curl -s -X POST \
      -H "X-Api-Key: $API_KEY" \
      -H "Content-Type: application/json" \
      "$RADARR_URL/api/v3/command" \
      -d "{\"name\":\"RefreshMovie\",\"movieIds\":[$MOVIE_ID]}")
    
    # Check if the refresh command succeeded
    REFRESH_ID=$(echo "$REFRESH_COMMAND" | jq '.id // empty')
    if [ -n "$REFRESH_ID" ]; then
      echo "Refresh command accepted (ID: $REFRESH_ID)."
      
      # Wait for the refresh to complete
      echo "Waiting for refresh to complete..."
      sleep 5
      
      # Step 2: Search for the movie using the MoviesSearch command that works with your Radarr
      echo "2. Searching for \"$MOVIE_TITLE\" using MoviesSearch command..."
      SEARCH_COMMAND=$(curl -s -X POST \
        -H "X-Api-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        "$RADARR_URL/api/v3/command" \
        -d "{\"name\":\"MoviesSearch\",\"movieIds\":[$MOVIE_ID]}")
      
      SEARCH_ID=$(echo "$SEARCH_COMMAND" | jq '.id // empty')
      if [ -n "$SEARCH_ID" ]; then
        echo "Search command accepted (ID: $SEARCH_ID)."
      else
        echo "Search command failed for \"$MOVIE_TITLE\". Response was:"
        echo "$SEARCH_COMMAND"
      fi
      
      # Wait a bit for search to initiate
      echo "Waiting for search operations to complete..."
      sleep 5
      
      # Step 3: Perform a "RescanMovie" command to check for any new downloads
      echo "3. Rescanning movie folder for \"$MOVIE_TITLE\"..."
      RESCAN_COMMAND=$(curl -s -X POST \
        -H "X-Api-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        "$RADARR_URL/api/v3/command" \
        -d "{\"name\":\"RescanMovie\",\"movieIds\":[$MOVIE_ID]}")
      
      RESCAN_ID=$(echo "$RESCAN_COMMAND" | jq '.id // empty')
      if [ -n "$RESCAN_ID" ]; then
        echo "Rescan command accepted (ID: $RESCAN_ID)."
      else
        echo "Rescan command not available or failed."
      fi
      
      # Mark as processed
      MOVIES_PROCESSED=$((MOVIES_PROCESSED + 1))
      
      # Sleep with full duration only after processing MAX_MOVIES
      if [ "$MOVIES_PROCESSED" -ge "$MAX_MOVIES" ]; then
        echo "Processed maximum number of movies. Sleeping for $SLEEP_DURATION seconds to avoid overloading indexers..."
        sleep "$SLEEP_DURATION"
      else
        echo "Movie refreshed. Sleeping for $REFRESH_DURATION seconds before continuing..."
        sleep "$REFRESH_DURATION"
      fi
    else
      echo "WARNING: Could not refresh \"$MOVIE_TITLE\". Response was:"
      echo "$REFRESH_COMMAND"
      echo "Skipping this movie."
      
      # Sleep a shorter time since we didn't actually do anything
      sleep 10
    fi
  done

  echo "Done. Processed $MOVIES_PROCESSED missing movies in this cycle."
  
  # If we didn't find any movies to process in this cycle, wait a bit before starting a new cycle
  if [ "$MOVIES_PROCESSED" -eq 0 ]; then
    echo "No missing movies processed this cycle. Waiting 60 seconds before starting a new cycle..."
    sleep 60
  fi
done
