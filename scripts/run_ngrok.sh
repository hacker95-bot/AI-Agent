#!/bin/bash
set -e

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
trap "kill $UVICORN_PID" EXIT

ngrok http 8000
