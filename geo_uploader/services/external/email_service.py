import logging

from flask_mail import Message

from geo_uploader.config import get_config
from geo_uploader.extensions import mail


class EmailService:
    def __init__(self, config=None, logger=None):
        self.config = config or get_config()
        self.logger = logger or logging.getLogger(__name__)

    def send_email(self, subject, recipient, body):
        msg = Message(subject, recipients=[recipient], body=body)
        try:
            mail.send(msg)
            return "Email sent!"
        except Exception as e:
            return f"Failed to send email. Error: {e}"
