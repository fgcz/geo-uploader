from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from geo_uploader.extensions import db
from geo_uploader.models.user_models import Users
from geo_uploader.utils.constants import STRING_LEN

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model

    from geo_uploader.models.user_models import Users
else:
    # For runtime, use the actual db.Model
    Model = db.Model


class UploadSessionModel(Model):
    __tablename__ = "upload_sessions"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    session_title = db.Column(db.String(2048))

    # Foreign key relationships
    users_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    user: Mapped["Users"] = relationship(
        "Users",
        foreign_keys=[users_id],
        uselist=False,
        back_populates="upload_sessions",
    )

    # Foreign key to reference the supervisor user
    supervisor_id: Mapped[int | None] = mapped_column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    supervisor: Mapped["Users | None"] = relationship(
        "Users",
        foreign_keys=[supervisor_id],
        back_populates="supervised_sessions",
        lazy=True,
    )

    md5_job_id: Mapped[int] = mapped_column(db.Integer, default=-1)
    md5_job_finished: Mapped[bool] = mapped_column(db.Boolean, default=False)
    upload_job_id: Mapped[int] = mapped_column(db.Integer, default=-1)

    remote_folder: Mapped[str | None] = mapped_column(
        db.String(STRING_LEN), nullable=True
    )

    # Metadata fields
    metadata_permission_user: Mapped[int] = mapped_column(db.Integer, nullable=False)
    metadata_study_length: Mapped[int] = mapped_column(db.Integer, default=11)
    metadata_contributors_number: Mapped[int] = mapped_column(db.Integer, default=7)
    metadata_supplementary_number: Mapped[int] = mapped_column(db.Integer, default=1)
    # you can derive the supplementary files number, but its cleaner to save it
    metadata_samples_displacement: Mapped[int] = mapped_column(db.Integer, default=0)
    metadata_samples_length: Mapped[int] = mapped_column(db.Integer, default=0)
    metadata_samples_width: Mapped[int] = mapped_column(db.Integer, default=20)
    metadata_protocol_displacement: Mapped[int] = mapped_column(db.Integer, default=0)
    metadata_protocol_length: Mapped[int] = mapped_column(db.Integer, default=13)
    metadata_datasteps_number: Mapped[int] = mapped_column(db.Integer, default=5)
    metadata_processedfiles_number: Mapped[int] = mapped_column(db.Integer, default=2)
    metadata_pairedend_displacement: Mapped[int] = mapped_column(db.Integer, default=0)

    @classmethod
    def get_by_id(cls, upload_id: int) -> "UploadSessionModel | None":
        result: UploadSessionModel | None = cls.query.filter_by(id=upload_id).first()
        return result

    @classmethod
    def session_title_exists(cls, session_title: str) -> bool:
        """Check if a session title already exists in the database."""
        return (
            db.session.query(cls).filter_by(session_title=session_title).first()
            is not None
        )
