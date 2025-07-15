from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user

from geo_uploader.forms import (
    DashboardDeleteSessionForm,
    DashboardDownloadForm,
    DashboardSearchForm,
    ProfileDetails,
    SessionRetrieveGEOForm,
)
from geo_uploader.models import UploadSessionModel, Users
from geo_uploader.services.profile_service import ProfileService
from geo_uploader.services.session_cache_service import SessionCacheService

main = Blueprint("main", __name__)


@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    # we do have a post request which could be csrf, but this view doesn't
    # have any function, so we look into csrf afterward
    is_admin = current_user.is_admin()

    search_sessions_query = request.args.get(
        "search_session", None
    )  # Get the search query from the URL parameters
    search_users_query = request.args.get(
        "search_user", None
    )  # Get the search query from the URL parameters

    query = UploadSessionModel.query

    if not is_admin:
        query = query.filter_by(users_id=current_user.id)

    # Apply filters based on the search queries
    if search_sessions_query:
        query = query.filter(
            UploadSessionModel.session_title.contains(search_sessions_query)
        )

    if search_users_query:
        query = query.join(Users, UploadSessionModel.users_id == Users.id).filter(
            Users.name.contains(search_users_query)
        )

    _all_uploadsessions = query.all()

    downloadForm = DashboardDownloadForm()
    searchForm = DashboardSearchForm()
    viewUploadForm = SessionRetrieveGEOForm()
    deleteSessionForm = DashboardDeleteSessionForm()
    return render_template(
        "main/dashboard.html",
        downloadForm=downloadForm,
        searchForm=searchForm,
        viewUploadForm=viewUploadForm,
        deleteSessionForm=deleteSessionForm,
        sessions=_all_uploadsessions,
        current_user_id=current_user.id,
        is_admin=is_admin,
    )


@main.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    return render_template("main/landing.html")


@main.route("/profile_details", methods=["GET", "POST"])
def profile_details():
    # using session because we haven't logged in yet potentially,
    user_login = SessionCacheService.get_current_user_login()
    if not user_login:
        flash("Please log in again, something went wrong.", "warning")
        return redirect(url_for("auth.login"))

    user = Users.query.filter_by(name=user_login).first()
    if not user:
        flash("User not found. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    if SessionCacheService.has_unfinished_profile():
        flash("Please enter the following information to complete the login", "warning")

    form = ProfileDetails()

    if form.validate_on_submit():
        profile_service = ProfileService()

        email = form.email.data
        remote_folder = form.remote_folder.data
        remote_password = form.remote_password.data
        full_name = form.full_name.data
        show_email = form.show_email.data
        safe_show_email = show_email if show_email is not None else False

        if not email or not remote_folder or not remote_password:
            flash("Email, folder and password are required", "error")
            return render_template("main/profile_details.html", form=form, user=user)

        success, message = profile_service.update_profile(
            user=user,
            email=email,
            remote_folder=remote_folder,
            remote_password=remote_password,
            full_name=full_name,
            show_email=safe_show_email,
        )

        if not success:
            flash(message, "danger")
            return render_template("main/profile_details.html", form=form, user=user)

        flash(message, "success")

        if SessionCacheService.has_unfinished_profile():
            SessionCacheService.clear_unfinished_profile()
            if login_user(user):
                flash("Login completed successfully", "success")
            else:
                flash("Profile updated but login failed", "danger")
        return redirect(url_for("main.index"))

    return render_template("main/profile_details.html", form=form, user=user)
