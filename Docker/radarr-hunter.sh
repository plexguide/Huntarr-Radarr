#!/usr/bin/env bash

# ---------------------------
# Configuration
# ---------------------------
# Use environment variables if provided; otherwise, fall back to defaults.
API_KEY=${RADARR_API_KEY:-"default_radarr_api_key"}
RADARR_URL=${RADARR_URL:-"http://10.0.0.10:7878"}
# How many movies to process before restarting the search cycle
MAX_MOVIES=${MAX_MOVIES:-1}
# Sleep duration in seconds after processing a movie (900=15min, 600=10min)
SLEEP_DURATION=${SLEEP_DURATION:-900}
# Set to true to pick movies randomly, false to go in order
RANDOM_SELECTION=${RANDOM_SELECTION:-true}

# ---------------------------
# Main infinite loop
# ---------------------------
while true; do
  echo "Retrieving movie data from Radarr..."
  # Get all movies from Radarr
  MOVIES_JSON=$(curl -s -H "X-Api-Key: $API_KEY" "$RADARR_URL/api/v3/movie")

  if [ -z "$MOVIES_JSON" ]; then
    echo "ERROR: Unable to retrieve movie data from Radarr. Retrying in 60 seconds..."
    sleep 60
    continue
  fi

  # Filter movies that do not have a file (i.e. missing files)
  INCOMPLETE_MOVIES_JSON=$(echo "$MOVIES_JSON" | jq '[.[] | select(.hasFile == false)]')
  TOTAL_INCOMPLETE=$(echo "$INCOMPLETE_MOVIES_JSON" | jq 'length')

  if [ "$TOTAL_INCOMPLETE" -eq 0 ]; then
    echo "No movies with missing files found in Radarr. Waiting 60 seconds before checking again..."
    sleep 60
    continue
  fi

  echo "Found $TOTAL_INCOMPLETE movie(s) with missing files."
  echo "Using ${RANDOM_SELECTION:+random}${RANDOM_SELECTION:-sequential} selection."
  echo "Will process up to ${MAX_MOVIES:-all} movies with a $SLEEP_DURATION second pause between each."

  MOVIES_PROCESSED=0
  ALREADY_CHECKED=()

  while true; do
    if [ "$MAX_MOVIES" -gt 0 ] && [ "$MOVIES_PROCESSED" -ge "$MAX_MOVIES" ]; then
      echo "Reached maximum number of movies to process ($MAX_MOVIES). Restarting search cycle..."
      break
    fi

    if [ ${#ALREADY_CHECKED[@]} -eq "$TOTAL_INCOMPLETE" ] || [ "$TOTAL_INCOMPLETE" -eq 0 ]; then
      echo "All movies have been checked. Waiting before starting a new cycle..."
      sleep 60
      break
    fi

    if [ "$RANDOM_SELECTION" = true ] && [ "$TOTAL_INCOMPLETE" -gt 1 ]; then
      while true; do
        INDEX=$((RANDOM % TOTAL_INCOMPLETE))
        if [[ ! " ${ALREADY_CHECKED[*]} " =~ " ${INDEX} " ]]; then
          break
        fi
      done
    else
      for ((i=0; i<TOTAL_INCOMPLETE; i++)); do
        if [[ ! " ${ALREADY_CHECKED[*]} " =~ " ${i} " ]]; then
          INDEX=$i
          break
        fi
      done
    fi

    ALREADY_CHECKED+=("$INDEX")
    MOVIE=$(echo "$INCOMPLETE_MOVIES_JSON" | jq ".[$INDEX]")
    MOVIE_ID=$(echo "$MOVIE" | jq '.id')
    MOVIE_TITLE=$(echo "$MOVIE" | jq -r '.title')

    echo "Selected movie \"$MOVIE_TITLE\" (ID: $MOVIE_ID) for processing..."
    echo "Sending command to search for missing movie \"$MOVIE_TITLE\" (ID: $MOVIE_ID)..."

    SEARCH_COMMAND=$(curl -s -X POST \
      -H "X-Api-Key: $API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"name\":\"MissingMovieSearch\",\"movieId\":$MOVIE_ID}" \
      "$RADARR_URL/api/v3/command")
    SEARCH_ID=$(echo "$SEARCH_COMMAND" | jq '.id // empty')

    if [ -n "$SEARCH_ID" ]; then
      echo "Search command accepted (ID: $SEARCH_ID)."
      MOVIES_PROCESSED=$((MOVIES_PROCESSED + 1))
      echo "Movie processed. Sleeping for $SLEEP_DURATION seconds..."
      sleep "$SLEEP_DURATION"
    else
      echo "WARNING: Search command did not return an ID. Response was:"
      echo "$SEARCH_COMMAND"
      echo "Skipping this movie."
      sleep 10
    fi
  done

  echo "Done. Processed $MOVIES_PROCESSED movies in this cycle."
  if [ "$MOVIES_PROCESSED" -eq 0 ]; then
    echo "No movies processed this cycle. Waiting 60 seconds before starting a new cycle..."
    sleep 60
  fi
done
