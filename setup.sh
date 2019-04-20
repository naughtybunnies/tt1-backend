#!/bin/sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
echo "FLASK IS STARTING"
ls -l
cd flask_app
ls -l


export FLASK_ENV=development
export FLASK_APP=main.py

flask run --host=0.0.0.0
