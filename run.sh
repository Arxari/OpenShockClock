#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PYTHON_SCRIPT="openshockclock.py"
REQUIREMENTS_FILE="requirements.txt"
VENV_DIR="$SCRIPT_DIR/venv"
REPO_URL="https://github.com/arxari/openshockclock.git" 
BRANCH="main"

PRESERVE_FILES=(".env" "config.txt")

update_script() {
    echo "Updating script from the repository..."
    
    TEMP_DIR=$(mktemp -d)

    if [ ! -d "$TEMP_DIR" ]; then
        echo "Failed to create temporary directory." >&2
        exit 1
    fi

    git clone --branch "$BRANCH" "$REPO_URL" "$TEMP_DIR"

    if [ $? -ne 0 ]; then
        echo "Failed to clone repository." >&2
        rm -rf "$TEMP_DIR"
        exit 1
    fi

    for file in "$TEMP_DIR"/*; do
        filename=$(basename "$file")
        if [[ ! " ${PRESERVE_FILES[@]} " =~ " ${filename} " ]]; then
            cp -r "$file" "$SCRIPT_DIR"
        fi
    done

    rm -rf "$TEMP_DIR"
}

update_script

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
