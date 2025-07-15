from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    StringField,
    SubmitField,
)
from wtforms.validators import InputRequired, Optional


class ProfileDetails(FlaskForm):
    """User profile configuration form.
    Manages user account settings including GEO submission credentials
    and visibility preferences. The show_email field controls whether
    the user appears in the bioinformatician selection list for other users.
    """

    email = EmailField("Email", [InputRequired()])
    show_email = BooleanField(
        "Show my name in the bioinformatician list", default=False
    )
    full_name = StringField("Full Name", [])
    remote_folder = StringField("GEO Remote repository", [InputRequired()])
    remote_password = StringField("GEO remote password", [InputRequired()])
    submit = SubmitField("Update")


# only used for the CSRF token
class DashboardDownloadForm(FlaskForm):
    submit = SubmitField("Download Metadata")


# only used for the CSRF token
class DashboardSearchForm(FlaskForm):
    search_session = StringField("Search sessions", validators=[Optional()])
    search_user = StringField("Search users", validators=[Optional()])
    submit = SubmitField("Filter")


# only used for the CSRF token
class DashboardDeleteSessionForm(FlaskForm):
    delete = SubmitField("Delete Session")
