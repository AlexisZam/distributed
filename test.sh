#!/usr/bin/env bash

host=$(hostname -I | egrep -o "192\.168\.1\.[0-9]{1,3}")

$src/backend/backend.py -h $host
