#!/bin/sh
trap "kill 0" EXIT

echo "Application starting..."

. venv/bin/activate

export FLASK_ENV=development
export FLASK_APP=main.py

echo "Starting backend service..."
flask run --host=0.0.0.0 &

sleep 2

echo "Starting frontend web application..."
cd build
python3 -m http.server 5001 &
python3 -m webbrowser http://localhost:5001/#/

wait