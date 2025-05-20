#!/bin/bash

# Check if the .env file exists
if [ ! -f "supabase/.env" ]; then
  echo "Error: supabase/.env file not found"
  exit 1
fi

# Extract the SERVICE_ROLE_KEY from the .env file
SERVICE_ROLE_KEY=$(grep "^SERVICE_ROLE_KEY=" supabase/.env | cut -d '=' -f 2-)

# Check if SERVICE_ROLE_KEY was found
if [ -z "$SERVICE_ROLE_KEY" ]; then
  echo "Error: SERVICE_ROLE_KEY not found in supabase/.env"
  exit 1
fi

# Print the SERVICE_ROLE_KEY
echo "$SERVICE_ROLE_KEY"