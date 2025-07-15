import os

from flask import Blueprint, abort, flash, redirect, url_for
from flask_login import login_required

from geo_uploader.decorators import session_owner_required
from geo_uploader.forms import (
    SessionDeleteGEOForm,
    SessionRetrieveGEOForm,
    SessionReuploadGEOForm,
)
from geo_uploader.models import UploadSessionModel
from geo_uploader.services.external.ftp_service import FTPService
from geo_uploader.services.file_service import FileService
from geo_uploader.services.session_cache_service import SessionCacheService

geo = Blueprint("geo", __name__)


@geo.route("/sessions/<id>/geo/retrieve", methods=["POST"])
@login_required
@session_owner_required
def retrieve_geo(id):
    """
    connects to FTP and saves to session the list of files on the session.remote_folder,
    can't trigger the post by hand, and have the ftp files uploaded
    """
    file_service = FileService()
    _session = UploadSessionModel.get_by_id(id)
    if _session is None:
        flash(f"Session with ID {id} not found", "error")
        return redirect(url_for("main.dashboard"))

    ftp_service = FTPService()
    form = SessionRetrieveGEOForm()
    if form.validate_on_submit():
        if _session.remote_folder is None:
            flash("Remote folder is not set, can not continue the operation", "warning")
            return redirect(url_for("progress.progress_session_upload", id=id))
        # When retrieving the / are used
        destination_folder = os.path.basename(
            file_service.get_session_folderpath(_session.session_title)
        )
        full_remote_folder = os.path.join(_session.remote_folder, destination_folder)
        ftp_files = ftp_service.list_files(
            full_remote_folder, _session.user.remote_password
        )
        SessionCacheService.store_progress_files_geo(ftp_files)

        flash("Files from FTP were gathered correctly!", "success")
        return redirect(url_for("progress.progress_session_upload", id=id))
    abort(403)


@geo.route("/sessions/<id>/geo/reupload", methods=["POST"])
@login_required
@session_owner_required
def reupload_files(id):
    form = SessionReuploadGEOForm()
    if form.validate_on_submit():
        flash("Reuploading of selected files job launched!", "success")
        return redirect(url_for("progress.progress_session_upload", id=id))
    abort(403)


@geo.route("/sessions/<id>/geo/delete", methods=["POST"])
@login_required
@session_owner_required
def delete_from_geo(id):
    """
    Gets the session, and the session owner and deletes the files in the geo repository linked to this session.
    """
    form = SessionDeleteGEOForm()
    ftp_service = FTPService()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return redirect(url_for("progress.progress_session_upload", id=id))

        project_title = f"{_session.session_title}"
        ftp_service.delete_folder(
            _session.remote_folder, project_title, _session.user.remote_password
        )

        flash("Files from FTP were deleted", "danger")
        return redirect(url_for("progress.progress_session_upload", id=id))
    abort(403)
