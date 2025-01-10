#!/bin/bash
set -e

VENV=/dexta/mounting/mounty-python

cd $VENV/

echo "Create venv"
python3 --version
python3 -m venv venv
. venv/bin/activate


echo "Install requirements"
pip install -r requirements.txt


echo "Running unmount all script"
if python3 unmount_all.py -eq 0
then
  echo Successful
else
  exit 1
fi
