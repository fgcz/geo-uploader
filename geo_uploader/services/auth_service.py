import logging
from enum import Enum

from geo_uploader.extensions import db
from geo_uploader.models import ADMIN, USER, Users

logger = logging.getLogger(__name__)


class AuthResult(Enum):
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_NOT_FOUND = "user_not_found"
    EMAIL_REQUIRED = "email_required"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    LOGIN_FAILED = "login_failed"


class AuthService:
    def authenticate_user(
        self, username: str, password: str
    ) -> tuple[AuthResult, Users | None, str | None]:
        """
        Authenticate user and return result with user object
        """
        try:
            # For registration-based auth, look up existing user
            user = Users.query.filter(Users.name.ilike(username)).first()

            if not user:
                return AuthResult.USER_NOT_FOUND, None, "User not found"

            # Validate password
            if not user.check_password(password):
                return AuthResult.INVALID_CREDENTIALS, None, "Invalid password"

            if user.email is None:
                return AuthResult.EMAIL_REQUIRED, user, "Email setup required"

            if not user.is_email_verified:
                return (
                    AuthResult.EMAIL_NOT_VERIFIED,
                    user,
                    "Please verify your email address first",
                )

            return AuthResult.SUCCESS, user, "Authentication successful"

        except Exception as e:
            logger.error(f"Unexpected authentication error for user {username}: {e!s}")
            return AuthResult.LOGIN_FAILED, None, "Authentication failed"

    def _get_or_create_user(self, username: str, auth_type: str) -> tuple[Users, bool]:
        user, is_new = Users.create_if_not_exists(name=username)

        target_role = ADMIN if auth_type == "Employee" else USER
        role_changed = False

        if user.role_code != target_role:
            user.role_code = target_role
            role_changed = True

        if is_new or role_changed:
            db.session.add(user)
            db.session.commit()

        return user, is_new
