#!/bin/sh
echo "Installing backend flask application"

python3 -m venv venv

. venv/bin/activate

pip install -r requirements.txt

echo "Installation finished.
    Run ./start to start the application"