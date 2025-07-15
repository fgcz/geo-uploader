from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

from geo_uploader.models import UploadSessionModel


def session_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = kwargs.get("id")  # Get session id from route
        if session_id is None:
            flash("Could not retrieve session id from arguments", "error")
            return redirect(url_for("main.dashboard"))

        try:
            session_id_int = int(session_id)
        except (ValueError, TypeError):
            flash("Could not cast session id argument into integer", "error")
            return redirect(url_for("main.dashboard"))
        _session = UploadSessionModel.get_by_id(session_id_int)

        if not _session:
            flash("Oops! Something went wrong! Session doesn't exist!", "danger")
            return redirect(url_for("main.dashboard"))

            # Admin = 1, user = 0
        if current_user.role_code != 1 and _session.users_id != current_user.id:
            # not admin and not owner
            flash(
                "Oops! Something went wrong! You don't have permission to access this page.",
                "warning",
            )
            return redirect(url_for("main.dashboard"))

        return f(*args, **kwargs)  # If authorized, proceed to the view

    return decorated_function
