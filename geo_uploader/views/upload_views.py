import logging

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from geo_uploader.decorators import session_owner_required
from geo_uploader.extensions import db
from geo_uploader.forms import (
    DashboardDeleteSessionForm,
    SessionGatherFilesForm,
    SessionNotifyArchiveForm,
)
from geo_uploader.models import UploadSessionModel, Users
from geo_uploader.services.external.directory_service import DirectoryService
from geo_uploader.services.external.email_service import EmailService
from geo_uploader.services.external.ftp_service import FTPService
from geo_uploader.services.external.job_service import JobService
from geo_uploader.services.file_service import FileService
from geo_uploader.services.sample_service import SampleService
from geo_uploader.services.session_cache_service import SessionCacheService
from geo_uploader.services.session_upload_service import (
    SessionMetadata,
    SessionUploadService,
)

logger = logging.getLogger(__name__)
upload = Blueprint("upload", __name__)

email_service = EmailService()


@upload.route("/sessions/new", methods=["GET"])
@login_required
def view_session_form():
    """Display the initial session creation form"""
    # Clear any existing session data when starting a new session
    SessionCacheService.clear_metadata()

    email_users_models = Users.get_email_list()
    email_users = [
        {"id": user.id, "full_name": user.full_name} for user in email_users_models
    ]

    new_session_files_form = SessionGatherFilesForm()
    new_session_files_form.remote_password.data = current_user.remote_password
    new_session_files_form.remote_folder.data = current_user.remote_folder
    if current_user.remote_password is None or current_user.remote_folder is None:
        flash("Please set your GEO FTP credentials in your Profile Details page", "danger")

    is_admin = current_user.is_admin()
    return render_template(
        "upload/new_session.html",
        new_session_files_form=new_session_files_form,
        email_users=email_users,
        is_admin=is_admin,
    )


@upload.route("/sessions/select-samples", methods=["POST"])
def view_sample_selection():
    """Process first form and display the file selection page"""
    email_users_models = Users.get_email_list()
    email_users = [
        {"id": user.id, "full_name": user.full_name} for user in email_users_models
    ]

    is_admin = current_user.is_admin()

    new_session_files_form = SessionGatherFilesForm()
    if not new_session_files_form.validate_on_submit():
        flash("Did you select your samples folder?", "danger")
        return render_template(
            "upload/new_session.html",
            new_session_files_form=new_session_files_form,
            email_users=email_users,
            is_admin=is_admin,
        )

    # Create metadata from form
    session_metadata = SessionMetadata.from_form(new_session_files_form)

    # Check if session title already exists
    if UploadSessionModel.session_title_exists(session_metadata.session_title):
        flash(
            "There exists already an upload session with this name! Please choose another title...",
            "danger",
        )
        return render_template(
            "upload/new_session.html",
            new_session_files_form=new_session_files_form,
            email_users=email_users,
            is_admin=is_admin,
        )

    session_metadata.is_single_cell = False
    SessionCacheService.store_session_metadata(session_metadata)

    folder_path = new_session_files_form.folder_modality_path.data
    remote_folder = new_session_files_form.remote_folder.data
    remote_password = new_session_files_form.remote_password.data
    if remote_folder == "None" or remote_password == "None":
        flash(
            "Please set your GEO remote folder and password on your Profile details page",
            "danger",
        )
        return render_template(
            "upload/new_session.html",
            new_session_files_form=new_session_files_form,
            email_users=email_users,
            is_admin=is_admin,
        )
    if not folder_path:
        flash("Folder path is required for folder modality", "danger")
        return render_template(
            "upload/new_session.html",
            new_session_files_form=new_session_files_form,
            email_users=email_users,
            is_admin=is_admin,
        )
    SessionCacheService.store_folder_path(folder_path)
    return redirect(url_for("upload.new_session_with_folder_selector"))


# @upload.route("/sessions/create", methods=["POST"])
# @login_required
# def create_session():
#     """Create a new upload session"""
#
#     # Get selected samples
#     selected_sample_names = request.form.getlist("sample_names")
#
#     # Get metadata from session
#     session_metadata = SessionCacheService.get_session_metadata()
#     if not session_metadata:
#         flash("Session data not found. Please start again.", "danger")
#         return redirect(url_for("upload.view_session_form"))
#
#     samples_metadata = SessionCacheService.filter_samples_metadata(
#         selected_sample_names
#     )
#     if not samples_metadata:
#         flash("Samples data not found. Please start again.", "danger")
#         return redirect(url_for("upload.view_session_form"))
#
#     try:
#         # Use service to handle all the complex operations
#         upload_service = SessionUploadService(db.session)
#         uploadsession = upload_service.create_upload_session(
#             session_metadata,
#             samples_metadata,
#             current_user,
#         )
#         db.session.add(uploadsession)
#         db.session.commit()
#         db.session.refresh(uploadsession)
#
#         # Clear session data when complete
#         SessionCacheService.clear_metadata()
#
#         flash("Your upload session is added successfully!", "success")
#         return redirect(url_for("main.dashboard"))
#
#     except Exception as e:
#         # Log the error
#         current_app.logger.error(f"Error creating upload session: {e!s}")
#         flash(f"An error occurred while creating your session: {e!s}", "danger")
#         return redirect(url_for("upload.view_session_form"))
#

@upload.route("/sessions/create/folder", methods=["POST"])
@login_required
def create_session_from_config():
    samplesData = request.get_json()
    sample_service = SampleService()
    # Get metadata from session
    session_metadata = SessionCacheService.get_session_metadata()
    if not session_metadata:
        flash("Session data not found. Please start again.", "danger")
        return redirect(url_for("upload.view_session_form"))

    samples_metadata = sample_service.get_samples_metadata_from_folder_selection(
        samplesData
    )

    if not samples_metadata:
        flash("Samples data empty. Please start again.", "danger")
        return redirect(url_for("upload.new_session_with_folder_selector"))
    try:
        # Use service to handle all the complex operations
        upload_service = SessionUploadService(db.session)
        uploadsession = upload_service.create_upload_session(
            session_metadata,
            samples_metadata,
            current_user,
        )
        db.session.add(uploadsession)
        db.session.commit()
        db.session.refresh(uploadsession)

        # Clear session data when complete
        SessionCacheService.clear_metadata()

        flash("Your upload session is created successfully!", "success")
        return redirect(url_for("main.dashboard"))

    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error creating upload session: {e!s}")
        flash(f"An error occurred while creating your session: {e!s}", "danger")
        return redirect(url_for("upload.new_session_with_folder_selector"))


@upload.route("/sessions/delete/<id>", methods=["POST"])
@login_required
@session_owner_required
def delete_session(id):
    """
    Delete from database
    Deletes the gather folder
    Cancels the jobs (in case they were running)
    Delete from GEO
    """
    file_service = FileService()
    job_service = JobService()
    ftp_service = FTPService()

    form = DashboardDeleteSessionForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return redirect(url_for("main.dashboard"))

        # delete from database
        db.session.delete(_session)
        db.session.commit()

        # delete the gather folder
        directory = file_service.get_session_folderpath(_session.session_title)
        file_service.delete_directory(directory)

        # Todo, what if the job is running
        job_service.delete_job(_session.md5_job_id)
        job_service.delete_job(_session.upload_job_id)

        # delete from GEO
        try:
            project_title = f"{_session.session_title}"
            ftp_service.delete_folder(
                _session.remote_folder, project_title, _session.user.remote_password
            )
        except Exception as e:
            logger.warning(f"Problem that the geo folder doesn't exist: {e}")
            flash("Your folder doesn't exist in GEO", "warning")
            return redirect(url_for("main.dashboard"))

        flash("Your session is deleted successfully!", "success")
        return redirect(url_for("main.dashboard"))
    abort(403)


@upload.route("/sessions/restore", methods=["POST"])
@login_required
def notify_restore():
    form = SessionNotifyArchiveForm()

    if form.validate_on_submit():
        supervisor_id = request.form.get("supervisor_id")
        if supervisor_id is None:
            flash("Could not find your supervisor.", "error")
            return redirect(url_for("upload.view_session_form"))
        supervisor = Users.get_by_id(int(supervisor_id))
        subject = "GeoUploader: Notification to restore archived data"
        body = (
            f"Dear {supervisor.name},\n\n"
            f"User {current_user.name} has selected you as their coach to their upload. "
            f"While entering the raw_path I have noticed the data has been archived!\n"
            f"{request.form.get('raw_folder')}\n\n"
            f"All the best,\n"
            f"GeoUploader - {current_user.name}"
        )
        email_service.send_email(subject, supervisor.email, body)

        flash(
            "Notification has been sent and the raw folder you provided will be unarchived. "
            "Continue with a different submission?",
            "success",
        )
        return redirect(url_for("upload.view_session_form"))
    abort(403)


@upload.route("/sessions/new/folder-selector", methods=["GET"])
@login_required
def new_session_with_folder_selector():
    session_metadata = SessionCacheService.get_session_metadata()
    folder_path = SessionCacheService.get_folder_path()

    if not session_metadata or not folder_path:
        flash("Session data not found. Please start again.", "error")
        return redirect(url_for("upload.view_session_form"))
    try:
        directory_service = DirectoryService()

        # Scan the directory for files
        files, file_count = directory_service.get_files_info(folder_path)

        logger.info(f"Found {file_count} files in {folder_path}")

        samples = {}

        for filename in files:
            sample_name = DirectoryService.extract_sample_name(filename)

            if sample_name not in samples:
                samples[sample_name] = {"raw": [], "processed": [], "unassigned": []}

            # Put ALL files in unassigned initially
            samples[sample_name]["unassigned"].append(filename)

        # Create the data structure expected by file_organizer.js
        result = {"samples": samples, "all_files": files, "folder_path": folder_path}

        return render_template("upload/file_organizer.html", data=result)

    except Exception as e:
        current_app.logger.error(f"Error processing folder: {e}")
        flash(
            f"Error accessing folder '{folder_path}'. Please ensure the folder exists and is accessible.",
            "error",
        )
        return redirect(url_for("upload.view_session_form"))


@upload.route("/api/infrastructure/tree", methods=["GET"])
def api_folder_tree():
    directory_service = DirectoryService()
    try:
        # Get query parameters
        start_path = request.args.get("path")

        # Get folder tree
        folders = directory_service.get_folder_tree(start_path=start_path)

        logger.info(f"Successfully retrieved {len(folders)} tree nodes")

        return jsonify({"success": True, "data": folders, "count": len(folders)})

    except Exception as e:
        logger.error(f"Exception caught: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )

    # folders = [
    #     {'id': 1, 'text': 'root', 'parent': '#', 'path': '/home/rdomi', 'type': 'folder'},
    #     {'id': 2, 'text': 'child1', 'parent': '1', 'path': '/home/rdomi', 'type': 'folder'},
    #     {'id': 3, 'text': 'child2', 'parent': '1', 'path': '/home/rdomi', 'type': 'folder'},
    #     {'id': 4, 'text': 'file1.txt', 'parent': '2', 'path': '/home/rdomi/file1.txt', 'type': 'file'},
    #     {'id': 5, 'text': 'file2.txt', 'parent': '2', 'path': '/home/rdomi/file2.txt', 'type': 'file'},
    # ]
    # return jsonify(folders)


@upload.route("/ajax/infrastructure/get_samples")
def get_folder_samples():
    """AJAX endpoint to get file count for a folder"""
    try:
        directory_service = DirectoryService()
        folder_path = request.args.get("path")

        if not folder_path:
            return jsonify({"error": "Path parameter is required"}), 400

        # Use the simplified method
        file_count = directory_service.count_files_in_directory(folder_path)

        return jsonify({"count": file_count, "status": "success"})

    except Exception as e:
        logger.error(f"Error getting folder samples: {e}")
        return jsonify({"error": f"An error occurred: {e!s}"}), 500
