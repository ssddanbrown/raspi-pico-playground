#!/bin/bash

# Simply copies a file to the pico's root directory.

file="$1"
filename="$(basename $file)"

rshell --buffer-size=512 --quiet "cp $file /pyboard/$filename"