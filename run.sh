#!/bin/bash
set -e

VENV=/dexta/mounting/mounty-python
ARGS=""

# Help function
function show_help() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --dry-run         Run the mount script in dry-run mode."
  echo "  --unmount-all     Unmount all our mounts"
  echo "  --cleanup         Clean up the fstab file."
  echo "  --help            Show this help message."
  exit 0
}

# Parse arguments
for arg in "$@"; do
  case $arg in
    --dry-run)
      ARGS="--dry-run"
      ;;
    --unmount-all)
      ARGS="--unmount-all"
      ;;
    --cleanup)
      ARGS="--cleanup"
      ;;
    --help)
      show_help
      ;;
    *)
      echo "Unknown argument: $arg"
      show_help
      ;;
  esac
done

# Navigate to the virtual environment directory
cd $VENV

# Create and activate the virtual environment
echo "Setting up virtual environment"
python3 --version
python3 -m venv venv
. venv/bin/activate

# Install requirements
echo "Installing requirements"
pip install -r requirements.txt

# Run the main Python script
echo "Running Python script with arguments: $ARGS"
if python3 run.py $ARGS; then
  echo "Successful"
else
  exit 1
fi
