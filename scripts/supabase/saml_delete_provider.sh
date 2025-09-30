#!/bin/bash

# Check if required argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <provider_id>"
    echo ""
    echo "Examples:"
    echo "  $0 '12345678-1234-1234-1234-123456789abc'"
    echo ""
    echo "💡 Use 'make saml-list-providers' to see available provider IDs"
    exit 1
fi

PROVIDER_ID="$1"

# 0. Try to remove existing .venv (if it exists)
rm -rf .venv

# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
python3 -m pip install --upgrade pip > /dev/null 2>&1
python3 -m pip install -r requirements.txt > /dev/null 2>&1

# 3. Run the script
python3 saml_delete_provider.py --provider-id "$PROVIDER_ID"

# 4. Clean up
deactivate
rm -rf .venv
