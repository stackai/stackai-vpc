#!/bin/bash

# Check if required arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <metadata_url> <domains>"
    echo ""
    echo "Examples:"
    echo "  $0 'https://idp.example.com/metadata' 'example.com'"
    echo "  $0 'https://idp.example.com/metadata' 'example.com,test.com'"
    exit 1
fi

METADATA_URL="$1"
DOMAINS="$2"
API_URL="${3:-http://localhost:8443}"

# 0. Try to remove existing .venv (if it exists)
rm -rf .venv

# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
python3 -m pip install --upgrade pip > /dev/null 2>&1
python3 -m pip install -r requirements.txt > /dev/null 2>&1

# 3. Run the script
python3 saml_add_provider.py --metadata-url "$METADATA_URL" --domains "$DOMAINS" --api-url "$API_URL"

# 4. Clean up
deactivate
rm -rf .venv
