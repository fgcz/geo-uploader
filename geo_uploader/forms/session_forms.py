from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
    StringField,
    SubmitField,
)
from wtforms.validators import InputRequired

from geo_uploader.utils.validators import validate_safe_path


class SessionGatherFilesForm(FlaskForm):
    """Main form for configuring upload sessions."""

    session_title = StringField(
        "Session Title", validators=[InputRequired(), validate_safe_path]
    )

    folder_modality_path = StringField()

    remote_folder = StringField("Geo remote repository", [InputRequired()])
    remote_password = StringField("Geo remote password", [InputRequired()])

    user_dropdown = StringField("Select your bioinformatician", validators=[])
    selected_user_id = HiddenField("User ID", validators=[])

    submit = SubmitField("Gather files")


# only used for CSRF
class SessionCreateSessionForm(FlaskForm):
    submit = SubmitField("Create session")


# only used for CSRF
class SessionNotifyArchiveForm(FlaskForm):
    # hidden field, used to pass supervisor to the email notification
    # supervisor_id = HiddenField(u'Supervisor Id', [])
    # raw_folder = HiddenField(u'Raw Folder', [])
    submit = SubmitField("Restore Files")


# only used for CSRF
class SessionRetrieveGEOForm(FlaskForm):
    submit = SubmitField("Retrieve GEO")


# only used for CSRF
class SessionDeleteGEOForm(FlaskForm):
    submit = SubmitField("Delete GEO")


# only used for CSRF
class SessionReuploadGEOForm(FlaskForm):
    submit = SubmitField("Reupload to GEO")
