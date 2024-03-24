#!/bin/bash

INPUT_FILE="$1"

# create media info
mediainfo -f "$INPUT_FILE" > "${INPUT_FILE}.mediainfo" && \
  # take 3 screenshots
  ffmpeg -ss 00:05:00 -y -i "$INPUT_FILE" -c:v png -frames:v 1 -loglevel error screenshot-1.png && \
  ffmpeg -ss 00:10:00 -y -i "$INPUT_FILE" -c:v png -frames:v 1 -loglevel error screenshot-2.png && \
  ffmpeg -ss 00:15:00 -y -i "$INPUT_FILE" -c:v png -frames:v 1 -loglevel error screenshot-3.png
