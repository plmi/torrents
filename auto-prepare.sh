#!/bin/bash

# usage ./<program> <source directory> <mount point> <destination directory> <announce url>

function log() {
  echo -e "\e[1m[\e[32m+\e[0m\e[1m]\e[0m ${1}"
}

SOURCE_DIRECTORY="$1"

# remove Sample and Proof directory
log "Strip Sample and Proof directory"
find "$SOURCE_DIRECTORY" -type d \( -iname 'Proof' -o -iname 'Sample' \) -exec rm -r {} + && \
find "$SOURCE_DIRECTORY" -type f \( -iname '*.proof.*' -o -iname '*.sample.*' -o -iname '*mediainfo.nfo' -o -iname "*usenet*" \) -exec rm -r {} + && \

# search for folders that match a dirname and trim {{.*}}
log "Sanitize directory names"
find "$SOURCE_DIRECTORY" -maxdepth 1 -type d -regex '.*-.+{{.*?}}$' -execdir sh -c 'mv "$1" "$(echo "$1" | sed "s/{{.*}}$//")"' sh {} \; && \
# if a folder just contains another folder move its files into parent directory
find "$SOURCE_DIRECTORY" -mindepth 2 -maxdepth 2 -type d -exec sh -c 'mv -t "${1}/../" "$1"/*' _ {} \; && \
# delete empty directories
find "$SOURCE_DIRECTORY" -mindepth 2 -maxdepth 2 -type d -empty -delete && \

# create mediainfo for each directory
log "Run mediainfo"
MOUNTPOINT="$2"
DESTINATION_PATH="$3"
find "$SOURCE_DIRECTORY" -type f \( -iname "*.mkv" -o -iname "*.iso" \) | while read -r file; do
  OUTPUT_JSON="$(basename "$(dirname "$(readlink -f "${file}")")").json"
  if [[ $file == *mkv ]]; then
    mediainfo --Output=JSON "$file" > "${DESTINATION_PATH}/$OUTPUT_JSON"
  elif [[ $file == *iso ]]; then
    # images need to be mounted first
    sudo umount "$MOUNTPOINT"
    sudo mount "$file" "$MOUNTPOINT" -o loop,ro && \
    # create mediainfo from largest file in /BDMV/STREAM
    largest_file=$(find "${MOUNTPOINT}/BDMV/STREAM/" -type f -exec du -a {} + | sort -nr | head -n 1 | cut -f2) && \
    mediainfo --Output=JSON "$largest_file" > "${DESTINATION_PATH}/$OUTPUT_JSON" && \
    sudo umount "$MOUNTPOINT"
  fi
done

# create torrent files
log "Create torrent files"
ANNOUNCE_URL="$4"
find "$SOURCE_DIRECTORY" -maxdepth 1 -type d -regex '.*-.+' | xargs -I {} \
  maketorrent --announce "${ANNOUNCE_URL}" --piece-length 24 \
  --private --name "${DESTINATION_PATH}/$(basename {})" {}

# move folders to destination
log "Move files to destination"
find "$SOURCE_DIRECTORY" -maxdepth 1 -type d -regex '.*-.+' -exec mv -t "${DESTINATION_PATH}" {} +
