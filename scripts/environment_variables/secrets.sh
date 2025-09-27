#!/bin/bash

# Script to expose the the instance secrets.

# Check if the .env file exists
if [ ! -f "supabase/.env" ]; then
  echo "Error: supabase/.env file not found"
  exit 1
fi

SERVICE_ROLE_KEY=$(grep "^SERVICE_ROLE_KEY=" supabase/.env | cut -d '=' -f 2-)
DASHBOARD_USERNAME=$(grep "^DASHBOARD_USERNAME=" supabase/.env | cut -d '=' -f 2-)
DASHBOARD_PASSWORD=$(grep "^DASHBOARD_PASSWORD=" supabase/.env | cut -d '=' -f 2-)

# Check if SERVICE_ROLE_KEY was found
if [ -z "$SERVICE_ROLE_KEY" ]; then
  echo "Error: SERVICE_ROLE_KEY not found in supabase/.env"
  exit 1
fi

if [ -z "$DASHBOARD_USERNAME" ]; then
  echo "Error: DASHBOARD_USERNAME not found in supabase/.env"
  exit 1
fi

if [ -z "$DASHBOARD_PASSWORD" ]; then
  echo "Error: DASHBOARD_PASSWORD not found in supabase/.env"
  exit 1
fi
# Print the SERVICE_ROLE_KEY
echo "SUPABASE INSTANCE CONFIGURATIONS"
echo "--------------------------------"
echo Service Role Key: "$SERVICE_ROLE_KEY"
echo Dashboard Username: "$DASHBOARD_USERNAME"
echo Dashboard Password: "$DASHBOARD_PASSWORD"
echo "--------------------------------"