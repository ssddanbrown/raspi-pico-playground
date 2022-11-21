#!/bin/bash

rshell --buffer-size=512 --quiet "cp $1 /pyboard/main.py; repl ~ import machine ~ machine.reset() ~"