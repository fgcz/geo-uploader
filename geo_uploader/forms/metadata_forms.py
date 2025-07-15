from flask_wtf import FlaskForm
from wtforms import SubmitField


# only used for CSRF
class MetadataNotifyReleaseForm(FlaskForm):
    submit = SubmitField("Request Release")


class MetadataNotifyHelpForm(FlaskForm):
    submit = SubmitField("Ask for help")


# only used for CSRF
class MetadataRequestPermissionForm(FlaskForm):
    submit = SubmitField("Request Permission")


# only used for CSRF
class MetadataReleaseBlockForm(FlaskForm):
    submit = SubmitField("Release Block")


# only used for CSRF
class MetadataStudyAddForm(FlaskForm):
    submit = SubmitField("Add to study")


# only used for CSRF
class MetadataProtocolAddForm(FlaskForm):
    submit = SubmitField("Add to protocol")


# only used for CSRF
class MetadataSaveForm(FlaskForm):
    submit = SubmitField("Save metadata")
