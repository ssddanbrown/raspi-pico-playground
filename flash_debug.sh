#!/bin/bash

rshell --buffer-size=512 --quiet "cp $1 /pyboard/dev.py; repl ~ import dev"