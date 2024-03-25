#!/bin/bash

# usage: <program> <movie path>
# creates a (regular, not full) mediainfo file and 3 screenshots
# in 5 minute intervals in the parent directory of the movie

INPUT_FILE="$(realpath "$1")"
OUTPUT_DIRECTORY="$(dirname "$INPUT_FILE")"

# create media info
mediainfo "$INPUT_FILE" > "${OUTPUT_DIRECTORY}.mediainfo" && \
  # take 3 screenshots
  ffmpeg -ss 00:05:00 -y -i "$INPUT_FILE" -c:v png -frames:v 1 -loglevel error "${OUTPUT_DIRECTORY}-screenshot-1.png" && \
  ffmpeg -ss 00:10:00 -y -i "$INPUT_FILE" -c:v png -frames:v 1 -loglevel error "${OUTPUT_DIRECTORY}-screenshot-2.png" && \
  ffmpeg -ss 00:15:00 -y -i "$INPUT_FILE" -c:v png -frames:v 1 -loglevel error "${OUTPUT_DIRECTORY}-screenshot-3.png"

echo "${OUTPUT_DIRECTORY}-screenshot-1.png"
echo "${OUTPUT_DIRECTORY}-screenshot-2.png"
echo "${OUTPUT_DIRECTORY}-screenshot-3.png"
