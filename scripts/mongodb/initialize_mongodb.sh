#!/bin/bash


#
# MONGODB INITIALIZATION SCRIPT
# 
# This script is used to populate the mongodb with the flow templates.

# 0. Try to remove existing .venv (if it exists)
rm -rf .venv

# 1. Create .venv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 2. Run the script
python3 add_templates.py