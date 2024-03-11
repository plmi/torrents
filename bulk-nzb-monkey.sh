#!/bin/bash

# usage: ./<binary> links.txt
# iterates over a list of nzb links and feeds them to nzb-monkey-go

LINKS="${1}"
[ -f "$LINKS" ] || { echo "File not found: $LINKS"; exit 1; }

while IFS= read -r line; do
    nzb-monkey-go "$line"
done < "$LINKS"
