import logging

from geo_uploader.extensions import db
from geo_uploader.models import Users
from geo_uploader.services.external.ftp_service import FTPService

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, ftp_service: FTPService | None = None):
        self.ftp_service = ftp_service or FTPService()

    def update_profile(
        self,
        user: Users,
        email: str,
        remote_folder: str,
        remote_password: str,
        show_email: bool,
        full_name: str | None = None,
    ) -> tuple[bool, str]:
        """
        Returns (success, message)
        """
        try:
            # Validate email uniqueness (your original logic)
            if email != user.email and Users.email_exists(email):
                return False, "Email already registered"

            # Test FTP connection (your original logic)
            if not self.ftp_service.test_connection(remote_folder, remote_password):
                return (
                    False,
                    "Could not connect to your GEO remote! Please check credentials.",
                )

            # Update user
            user.email = email
            user.remote_folder = remote_folder
            user.remote_password = remote_password
            if full_name is not None:
                user.full_name = full_name
            user.preferences_email_list = show_email

            db.session.commit()
            return True, "Profile updated successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update profile for user {user.name}: {e!s}")
            return False, f"Failed to update profile: {e!s}"
