#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "PYTHONPATH set to: $PYTHONPATH"
else
    echo ".env file not found. PYTHONPATH not set."
fi
