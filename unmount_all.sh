#!/bin/bash
set -e

VENV=/dexta/mounting/mounty-python

# Confirmation prompt
echo "This script will unmount all shares on the VM with the specified prefix (usually /shares)"
read -p "Are you sure you want to proceed? (yes to confirm): " CONFIRMATION

if [[ "$CONFIRMATION" != "yes" ]]; then
    echo "Operation aborted."
    exit 1
fi

# Navigate to the virtual environment directory
cd $VENV/

# Create a virtual environment
echo "Create venv"
python3 --version
python3 -m venv venv
. venv/bin/activate

# Install requirements
echo "Install requirements"
pip install -r requirements.txt

# Run the unmount_all script
echo "Running unmount all script"
if python3 unmount_all.py; then
    echo "Successful"
else
    exit 1
fi
