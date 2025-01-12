#!/bin/bash
set -e

VENV=/dexta/mounting/mounty-python
DRY_RUN_ARG=""

# Help function
function show_help() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --dry-run    Run mounty-python in dry-run mode."
  echo "  --help       Show this help message."
  exit 0
}

# Parse arguments
for arg in "$@"; do
  case $arg in
    --dry-run)
      DRY_RUN_ARG="--dry-run"
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

## Navigate to virtual environment directory
#cd $VENV
#
## Create virtual environment
#echo "Create venv"
#python3 --version
#python3 -m venv venv
#. venv/bin/activate
#
## Install requirements
#echo "Install requirements"
#pip install -r requirements.txt

# Run the mount script
echo "Run mount script"
if python3 run.py $DRY_RUN_ARG; then
  echo "Successful"
else
  exit 1
fi
