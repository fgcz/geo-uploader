#!/usr/bin/env python3

import sys
import os
import subprocess
import shutil
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

    # Check if conda is available
    conda_cmd = shutil.which("conda")
    if not conda_cmd:
        print("Error: conda not found or not properly initialized")
        print("Please ensure conda is installed and available in PATH")
        sys.exit(1)

    # Activate environment and run the Python script
    try:
        # For cross-platform conda activation, we'll use subprocess with shell=True
        # and construct the command to activate environment and run python

        if os.name == 'nt':  # Windows
            # Use cmd.exe for Windows
            activate_cmd = f'conda activate gi_geo-uploader && '
        else:  # Unix-like (Linux, Mac)
            # Use bash for Unix-like systems
            activate_cmd = f'eval "$(conda shell.bash hook)" && conda activate gi_geo-uploader && '

        # Set PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = PYTHON_PATH

        # Construct the full command
        python_cmd = f'{activate_cmd}python -m {PYTHON_MODULE} {script_options}'

        # Open output files for logging
        with open(OUTPUT_PATH, 'a') as stdout_f, open(ERROR_PATH, 'a') as stderr_f:
            # Create a custom class to handle dual output (console + file)
            class DualOutput:
                def __init__(self, file_obj, console_obj):
                    self.file = file_obj
                    self.console = console_obj

                def write(self, text):
                    self.file.write(text)
                    self.file.flush()
                    self.console.write(text)
                    self.console.flush()

                def flush(self):
                    self.file.flush()
                    self.console.flush()

            # Save original stdout/stderr
            original_stdout = sys.stdout
            original_stderr = sys.stderr

            # Redirect to dual output
            sys.stdout = DualOutput(stdout_f, original_stdout)
            sys.stderr = DualOutput(stderr_f, original_stderr)

            try:
                print("Successfully activated gi_geo-uploader environment")

                # Run the command
                result = subprocess.run(
                    python_cmd,
                    shell=True,
                    env=env,
                    text=True
                )

                exit_code = result.returncode

            finally:
                # Restore original stdout/stderr
                sys.stdout = original_stdout
                sys.stderr = original_stderr

    except Exception as e:
        print(f"Error: Failed to activate gi_geo-uploader environment or run script: {e}")

        # Try to list available environments for debugging
        try:
            print("Available environments:")
            subprocess.run([conda_cmd, "env", "list"], check=False)
        except:
            pass

        sys.exit(1)

    # Check exit status
    if exit_code == 0:
        print("Script completed successfully.")
    else:
        print(f"Script failed with exit code {exit_code}.")

    print(f"End time: {datetime.now()}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()