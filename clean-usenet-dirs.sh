#!/bin/bash

find "$1" -maxdepth 1 -type d -regex '.*-.+{{.*?}}$' -execdir sh -c 'mv "$1" "$(echo "$1" | sed "s/{{.*}}$//")"' sh {} \;
