#!/bin/bash

OUTPUT_PATH=REPLACE_OUTPUT_PATH
ERROR_PATH=REPLACE_ERROR_PATH
exec > >(tee -a "$OUTPUT_PATH") 2> >(tee -a "$ERROR_PATH" >&2)
# The variables which start with REPLACE will be changed by python on run.

eval "$(conda shell.bash hook)" 2>/dev/null || {
    echo "Error: conda not found or not properly initialized"
    echo "Please ensure conda is installed and run: conda init bash"
    exit 1
}

# Activate environment
if conda activate gi_geo-uploader; then
    echo "Successfully activated gi_geo-uploader environment"
else
    echo "Error: Failed to activate gi_geo-uploader environment"
    echo "Available environments:"
    conda env list
    exit 1
fi

# Configuration from command line arguments
SCRIPT_OPTIONS="$1"

# Validate arguments
if [ -z "$SCRIPT_OPTIONS" ]; then
    echo "Error: Missing script options"
    exit 1
fi

# Run the Python uploader script
echo "Starting script with options: $SCRIPT_OPTIONS"

export PYTHONPATH=REPLACE_PYTHON_PATH
python -m REPLACE_PYTHON_MODULE $SCRIPT_OPTIONS

# Check exit status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Script completed successfully."
else
    echo "Script failed with exit code $EXIT_CODE."
fi

echo "End time: $(date)"
exit $EXIT_CODE
