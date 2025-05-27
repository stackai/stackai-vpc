#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- StackAI Onprem Puller (Python ZIP Method) ---"

# Determine the script's own directory to locate puller.py and requirements.txt
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PULLER_SCRIPT="$SCRIPT_DIR/puller.py"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# Define a temporary virtual environment directory within scripts/update
VENV_DIR="$SCRIPT_DIR/.puller_venv"

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install Python 3."
    exit 1
fi

# Check for pip with python3
if ! python3 -m pip --version &> /dev/null; then
    echo "Error: pip for python3 is not available. Please ensure pip is installed for your Python 3 environment."
    exit 1
fi

echo "Setting up temporary Python virtual environment at $VENV_DIR..."
if [ -d "$VENV_DIR" ]; then
  echo "Existing venv found. Removing and recreating."
  rm -rf "$VENV_DIR"
fi
python3 -m venv "$VENV_DIR"

# Activate the virtual environment
unset PYTHONHOME
unset PYTHONPATH
source "$VENV_DIR/bin/activate"

echo "Installing dependencies from $REQUIREMENTS_FILE into the virtual environment..."
if ! python3 -m pip install --quiet -r "$REQUIREMENTS_FILE"; then
    echo "Error: Failed to install Python dependencies."
    echo "Deactivating and removing temporary venv."
    deactivate
    rm -rf "$VENV_DIR"
    exit 1
fi
echo "Dependencies installed."

echo "Running Python puller script: $PULLER_SCRIPT..."
if ! python3 "$PULLER_SCRIPT"; then
    echo "Error: Python puller script failed."
    deactivate
    rm -rf "$VENV_DIR"
    exit 1
fi

# Deactivate and remove the virtual environment
echo "Update script finished. Cleaning up virtual environment..."
deactivate
rm -rf "$VENV_DIR"

echo "--- Python ZIP Puller Finished Successfully ---" 