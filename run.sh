#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

PYTHON_SCRIPT="$SCRIPT_DIR/openshockclock.py"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating a virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing packages from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE"

    if [ $? -ne 0 ]; then
        echo "Failed to install packages." >&2
        deactivate
        exit 1
    fi
else
    echo "Error: requirements.txt not found." >&2
    deactivate
    exit 1
fi

clear

python "$PYTHON_SCRIPT"

if [ $? -ne 0 ]; then
    echo "The Python script encountered an error." >&2
    deactivate
    exit 1
fi

deactivate
