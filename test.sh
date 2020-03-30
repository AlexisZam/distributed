#!/usr/bin/env bash

SRC_DIR=src

# host=$(hostname -I | egrep -o "192\.168\.1\.[0-9]{1,3}")
host=127.0.0.1
port=5000

n_nodes=5

for node in $(seq 0 $((n_nodes - 1))); do
    $SRC_DIR/backend/backend.py -h $host -p $port &
    sleep 2
    $SRC_DIR/backend/test.py -h $host -p $port &
    ((port++))
done
