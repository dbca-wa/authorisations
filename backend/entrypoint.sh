#!/usr/bin/env bash

echo "Launching gunicorn..."
exec gunicorn config.wsgi --bind 0.0.0.0:8080 --timeout 300 --graceful-timeout 90 --max-requests 2048 --workers 4 --preload
