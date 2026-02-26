#!/usr/bin/env python3

import shlex
import sys
import os
import subprocess
from datetime import datetime


def main():
    OUTPUT_PATH = "REPLACE_OUTPUT_PATH"
    ERROR_PATH = "REPLACE_ERROR_PATH"
    PYTHON_PATH = "REPLACE_PYTHON_PATH"
    PYTHON_MODULE = "REPLACE_PYTHON_MODULE"

    # Configuration from command line arguments
    if len(sys.argv) < 2:
        print("Error: Missing script options")
        sys.exit(1)

    script_options = sys.argv[1]
    print(f"Starting script with options: {script_options}")
    print(f"Start time: {datetime.now()}")

    env = os.environ.copy()
    env['PYTHONPATH'] = PYTHON_PATH

    # Split the options string into individual arguments
    options_list = shlex.split(script_options)
    python_cmd = [sys.executable, "-m", PYTHON_MODULE] + options_list

    # Open output files for logging and run the subprocess
    with open(OUTPUT_PATH, 'a') as stdout_f, open(ERROR_PATH, 'a') as stderr_f:
        # Run the command with stdout/stderr redirected to files
        result = subprocess.run(
            python_cmd,
            stdout=stdout_f,
            stderr=stderr_f,
            text=True,
            env=env
        )

        exit_code = result.returncode

    # Check exit status
    if exit_code == 0:
        print("Script completed successfully.")
    else:
        print(f"Script failed with exit code {exit_code}.")

    print(f"End time: {datetime.now()}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()