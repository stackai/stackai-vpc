#!/bin/bash
set -e

# 1. Create .venv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the script

python3 update.py

# 3. Deactivate the virtual environment
deactivate

# 4. Remove the .venv directory
rm -rf .venv
