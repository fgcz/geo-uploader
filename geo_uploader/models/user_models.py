from typing import TYPE_CHECKING, Optional

from flask_admin.contrib import sqla
from flask_login import UserMixin, current_user
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from geo_uploader.extensions import db
from geo_uploader.models.user_constants import ADMIN, USER, USER_ROLE
from geo_uploader.utils.constants import STRING_LEN

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model

    from geo_uploader.models.upload_sessions import UploadSessionModel
else:
    # For runtime, use the actual db.Model
    Model = db.Model


class Users(Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)

    # Authentication fields
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_activation_key: Mapped[str | None] = mapped_column(
        String(STRING_LEN), nullable=True
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # User information
    name: Mapped[str] = mapped_column(db.String(STRING_LEN), unique=True)
    full_name: Mapped[str] = mapped_column(db.String(STRING_LEN), unique=True)
    email: Mapped[str] = mapped_column(db.String(STRING_LEN), unique=True)

    role_code: Mapped[int] = mapped_column(
        db.SmallInteger, default=USER, nullable=False
    )

    # Preferences
    preferences_email_list: Mapped[bool | None] = mapped_column(db.Boolean)

    # Remote connection settings
    remote_folder: Mapped[str | None] = mapped_column(
        db.String(STRING_LEN), nullable=True
    )
    remote_password: Mapped[str | None] = mapped_column(
        db.String(STRING_LEN), nullable=True
    )

    upload_sessions: Mapped[list["UploadSessionModel"]] = relationship(
        "UploadSessionModel",
        foreign_keys="UploadSessionModel.users_id",
        back_populates="user",
    )

    supervised_sessions: Mapped[list["UploadSessionModel"]] = relationship(
        "UploadSessionModel",
        foreign_keys="UploadSessionModel.supervisor_id",
        back_populates="supervisor",
    )

    @property
    def password(self) -> str:
        """Password getter - raises AttributeError to prevent reading."""
        raise AttributeError("Password is not readable")

    @password.setter
    def password(self, password: str) -> None:
        """Set password hash from plain password."""
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password)

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def role(self) -> str:
        return USER_ROLE.get(self.role_code)

    def is_admin(self) -> bool:
        return self.role_code == ADMIN

    def is_authenticated(self) -> bool:
        return True

    @classmethod
    def authenticate(cls, name: str, password: str) -> tuple[Optional["Users"], bool]:
        """Authenticate user by name and password."""
        if not name or not password:
            return None, False

        user = cls.query.filter(Users.name.ilike(name)).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    def verify_email(self) -> None:
        """Mark email as verified and clear activation key."""
        self.is_email_verified = True
        self.email_activation_key = None

    def is_email_verified_user(self) -> bool:
        """Check if user's email is verified."""
        return self.is_email_verified

    @classmethod
    def get_by_id(cls, user_id: int) -> "Users":
        result: Users = cls.query.filter_by(id=user_id).first_or_404()
        return result

    @classmethod
    def get_email_by_id(cls, user_id: int) -> str:
        user: Users = cls.query.filter_by(id=user_id).first_or_404()
        result: str = user.email
        return result

    @classmethod
    def create_if_not_exists(
        cls, name: str | None, email: str = None, **kwargs
    ) -> tuple["Users", bool]:
        """Create user if doesn't exist, return (user, created)."""
        if not name:
            raise ValueError("Username is required")

        user = cls.query.filter_by(name=name).first()
        if not user:
            user_data = {"name": name}
            if email:
                user_data["email"] = email
            user_data.update(kwargs)

            user = cls(**user_data)
            db.session.add(user)
            return user, True
        return user, False

    @classmethod
    def email_exists(cls, email: str) -> bool:
        """Check if a session title already exists in the database."""
        return db.session.query(cls).filter_by(email=email).first() is not None

    @classmethod
    def get_email_list(cls) -> list["Users"]:
        """
        Returns a list of users where role_code is 1 and preferences_email_list is True.
        """
        result = cls.query.filter_by(role_code=1, preferences_email_list=True).all()
        return result

    def __unicode__(self):
        return f"{self.id}. {self.name}"


class UsersAdmin(sqla.ModelView):
    column_list = (
        "id",
        "name",
        "full_name",
        "email",
        "role_code",
        "preferences_email_list",
    )
    column_sortable_list = (
        "id",
        "role_code",
        "name",
        "email",
        "preferences_email_list",
    )
    column_searchable_list = ("email", Users.email)
    column_filters = (
        "id",
        "name",
        "email",
        "role_code",
        "full_name",
        "preferences_email_list",
    )

    form_excluded_columns = "password"

    def __init__(self, session):
        super().__init__(Users, session)

    def is_accessible(self):
        if current_user.role == "admin":
            return current_user.is_authenticated()
