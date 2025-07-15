import json
import logging
import os
import sys
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from geo_uploader.config import get_config

logger = logging.getLogger(__name__)


class JobService:
    """Service for handling background job submissions on local machines"""

    # Class-level job tracking
    _jobs: dict[int, dict[str, Any]] = {}
    _next_job_id: int = 1
    _lock = threading.Lock()

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        # Create jobs directory for tracking
        self._jobs_dir = Path(get_config().JOB_PATH)

        self._jobs_dir.mkdir(parents=True, exist_ok=True)
        self._load_existing_jobs()

    def _load_existing_jobs(self):
        """Load existing jobs from disk on startup"""
        jobs_file = self._jobs_dir / "jobs.json"
        if jobs_file.exists():
            try:
                with open(jobs_file) as f:
                    data = json.load(f)
                    self._jobs = data.get("jobs", {})
                    # Convert string keys back to int
                    self._jobs = {int(k): v for k, v in self._jobs.items()}
                    self._next_job_id = data.get("next_id", 1)
            except Exception as e:
                self.logger.warning(f"Could not load existing jobs: {e}")

    def _save_jobs(self):
        """Save jobs state to disk"""
        jobs_file = self._jobs_dir / "jobs.json"
        try:
            # Convert int keys to strings for JSON
            jobs_data = {str(k): v for k, v in self._jobs.items()}
            data = {"jobs": jobs_data, "next_id": self._next_job_id}
            with open(jobs_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save jobs state: {e}")

    def _get_next_job_id(self) -> int:
        """Get the next available job ID"""
        with self._lock:
            job_id = self._next_job_id
            self._next_job_id += 1
            return job_id

    def _run_script_in_background(
        self, job_id: int, script_path: str, script_options: str = ""
    ):
        """Run the script in a background thread"""
        try:
            # Update job status to running
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id].update(
                        {"status": "RUNNING", "start_time": datetime.now().isoformat()}
                    )
                    self._save_jobs()

            # Prepare command
            cmd = [sys.executable, script_path]
            if script_options:
                cmd = [sys.executable, script_path, script_options]

            # Create log files
            job_info = self._jobs[job_id]
            log_dir = Path(job_info["log_dir"])
            log_dir.mkdir(parents=True, exist_ok=True)

            stdout_file = log_dir / f"{job_info['name']}.out"
            stderr_file = log_dir / f"{job_info['name']}.err"

            # Run the process
            start_time = time.time()
            with open(stdout_file, "w") as stdout_f, open(stderr_file, "w") as stderr_f:
                process = subprocess.run(
                    cmd,
                    stdout=stdout_f,
                    stderr=stderr_f,
                    text=True,
                    cwd=os.path.dirname(script_path),
                )

            end_time = time.time()
            elapsed = end_time - start_time

            # Update job status based on result
            with self._lock:
                if job_id in self._jobs:
                    status = "COMPLETED" if process.returncode == 0 else "FAILED"
                    self._jobs[job_id].update(
                        {
                            "status": status,
                            "return_code": process.returncode,
                            "elapsed": f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}",
                            "end_time": datetime.now().isoformat(),
                            "stdout_file": str(stdout_file),
                            "stderr_file": str(stderr_file),
                        }
                    )
                    self._save_jobs()

            self.logger.info(f"Job {job_id} completed with status: {status}")

        except Exception as e:
            # Update job status to failed
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id].update(
                        {
                            "status": "FAILED",
                            "error": str(e),
                            "end_time": datetime.now().isoformat(),
                        }
                    )
                    self._save_jobs()

            self.logger.error(f"Job {job_id} failed with error: {e}")

    def launch_script(
        self, script_path: str, job_name: str, script_options: str = ""
    ) -> dict[str, Any]:
        """
        Launch a script as a background job.

        Args:
            script_path: str
                Path to the script to execute
            script_options: str
                Options to pass to the script

        Returns:
            Dictionary with job information
        """
        if not os.path.exists(script_path):
            return {
                "success": False,
                "error": f"Script not found: {script_path}",
                "message": "Failed to submit job: script not found",
            }

        try:
            # Generate job ID and name
            job_id = self._get_next_job_id()

            # Set up log directory (in the same directory as the script)
            log_dir = Path(script_path).parent / "jobs"

            # Store job information
            with self._lock:
                self._jobs[job_id] = {
                    "job_id": job_id,
                    "name": job_name,
                    "script_path": script_path,
                    "script_options": script_options,
                    "status": "PENDING",
                    "submit_time": datetime.now().isoformat(),
                    "log_dir": str(log_dir),
                }
                self._save_jobs()

            # Start the job in a background thread
            thread = threading.Thread(
                target=self._run_script_in_background,
                args=(job_id, script_path, script_options),
                daemon=True,
            )
            thread.start()

            return {
                "success": True,
                "job_id": job_id,
                "message": f"Job submitted successfully with ID: {job_id}",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "An unexpected error occurred while submitting the job",
            }

    def get_job_info(self, job_id: int) -> dict[str, Any] | None:
        """
        Get information about a specific job.

        Args:
            job_id: The ID of the job to check

        Returns:
            Dictionary with job information or None if not found
        """
        if job_id is None:
            return None

        with self._lock:
            job_info = self._jobs.get(job_id)
            if job_info:
                # Return a copy to avoid external modifications
                return job_info.copy()
            return None

    def delete_job(self, job_id: int) -> bool:
        """
        Cancel/delete a job.

        Args:
            job_id: The ID of the job to cancel

        Returns:
            True if job was found and cancelled, False otherwise
        """
        try:
            with self._lock:
                if job_id in self._jobs:
                    job_info = self._jobs[job_id]
                    if job_info["status"] in ["PENDING", "RUNNING"]:
                        # For running jobs, we can't easily kill them in this simple implementation
                        # Just mark as cancelled
                        job_info.update(
                            {
                                "status": "CANCELLED",
                                "end_time": datetime.now().isoformat(),
                            }
                        )
                        self._save_jobs()
                        self.logger.info(f"Job {job_id} marked as cancelled")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error cancelling job {job_id}: {e}")
            return False

    def get_all_jobs(self) -> dict[int, dict[str, Any]]:
        """Get information about all jobs"""
        with self._lock:
            return {k: v.copy() for k, v in self._jobs.items()}

    def cleanup_old_jobs(self, days: int = 30):
        """Remove job records older than specified days"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        with self._lock:
            jobs_to_remove = []
            for job_id, job_info in self._jobs.items():
                try:
                    submit_time = datetime.fromisoformat(
                        job_info["submit_time"]
                    ).timestamp()
                    if submit_time < cutoff_time and job_info["status"] in [
                        "COMPLETED",
                        "FAILED",
                        "CANCELLED",
                    ]:
                        jobs_to_remove.append(job_id)
                except Exception:
                    continue

            for job_id in jobs_to_remove:
                del self._jobs[job_id]

            if jobs_to_remove:
                self._save_jobs()
                self.logger.info(f"Cleaned up {len(jobs_to_remove)} old job records")

    @staticmethod
    def prepare_script(
        template_script_path: str,
        destination_script_path: str,
        python_script: str,
        job_name: str,
    ):
        """
        Prepare a job script by copying template and replacing placeholders.

        Args:
            template_script_path: Template script path
            destination_script_path: Destination path for the prepared script
            python_script: Python script to be run
            job_name: Display name for the job
        """
        try:
            # Copy template to destination
            shutil.copy(template_script_path, destination_script_path)

            # Create jobs directory
            jobs_dir = Path(destination_script_path).parent / "jobs"
            jobs_dir.mkdir(exist_ok=True)

            # Define replacements for a simple shell script
            python_path = Path(
                python_script
            ).parent.parent.parent  # Go up to project root
            module_name = Path(python_script).stem

            replacements = {
                "REPLACE_JOB_NAME": job_name,
                "REPLACE_OUTPUT_PATH": str(jobs_dir / f"{job_name}.out").replace(
                    "\\", "\\\\"
                ),
                "REPLACE_ERROR_PATH": str(jobs_dir / f"{job_name}.err").replace(
                    "\\", "\\\\"
                ),
                "REPLACE_PYTHON_PATH": str(python_path).replace(
                "\\", "\\\\"
                ),
                "REPLACE_PYTHON_MODULE": f"utils.upload_scripts.{module_name}",
            }

            # Read and modify the script
            with open(destination_script_path) as f:
                content = f.read()

            for placeholder, value in replacements.items():
                content = content.replace(placeholder, value)

            # Write back the modified script
            with open(destination_script_path, "w") as f:
                f.write(content)

            # Make script executable
            os.chmod(destination_script_path, 0o755)

        except Exception as e:
            logger.error(f"Error preparing script {destination_script_path}: {e}")
            raise
