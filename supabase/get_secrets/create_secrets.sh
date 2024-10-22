#! /bin/bash

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and create credentials
pip install -r requirements.txt
python create_credentials.py

# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf .venv
