#!/usr/bin/env bash

CMD_NAME=$(basename "$0")

printf '%s' "$*" > "/tmp/last_${CMD_NAME}_cmd.txt"
