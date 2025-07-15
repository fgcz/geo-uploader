from flask import Blueprint, flash, jsonify, redirect, render_template, url_for
from flask_login import login_required

from geo_uploader.decorators import session_owner_required
from geo_uploader.extensions import db
from geo_uploader.forms import (
    SessionDeleteGEOForm,
    SessionRetrieveGEOForm,
    SessionReuploadGEOForm,
)
from geo_uploader.models import UploadSessionModel
from geo_uploader.services.excel_service import ExcelService
from geo_uploader.services.external.email_service import EmailService
from geo_uploader.services.external.job_service import JobService
from geo_uploader.services.file_service import FileService
from geo_uploader.services.sample_parser_service import SampleParserService
from geo_uploader.services.sample_service import SampleService
from geo_uploader.services.session_cache_service import SessionCacheService
from geo_uploader.utils.constants import STATUS_CLASS

# Create services
progress = Blueprint("progress", __name__)


@progress.route("/sessions/<id>/progress/md5", methods=["GET"])
@login_required
@session_owner_required
def progress_session_md5(id):
    """
    Gets the job_info

    Gets the local files from files_size.txt
    Gets the md5sheet.tsv completed md5sum
    Compares them for discrepancies
    """
    _session = UploadSessionModel.get_by_id(id)
    if _session is None:
        flash(f"Session with ID {id} not found", "error")
        return redirect(url_for("main.dashboard"))

    job_service = JobService()
    sample_service = SampleService()
    file_service = FileService()
    sample_parser_service = SampleParserService()

    job_info = job_service.get_job_info(_session.md5_job_id)
    status_class = STATUS_CLASS.get(job_info["status"]) if job_info else "NO_JOB_STATUS"
    upload_samples_path = file_service.get_session_folderpath(
        _session.session_title, "upload_samples.ini"
    )
    local_samples = sample_parser_service.get_samples_from_ini(upload_samples_path)

    md5sheet_path = file_service.get_session_folderpath(
        _session.session_title, "md5sheet.tsv"
    )

    md5_samples = sample_parser_service.get_md5_files_from_tsv(md5sheet_path)
    discrepancies = (
        sample_service.compare_sample_md5(
            local_samples, md5_samples, compare_size=False
        )
        if md5_samples
        else None
    )
    # print('disc: ', discrepancies)
    discrepancies = []
    return render_template(
        "progress/md5_progress.html",
        job_info=job_info,
        name=_session.session_title,
        status_class=status_class,
        discrepancies=discrepancies,
        local_samples=local_samples,
        md5_samples=md5_samples,
    )


@progress.route("/sessions/<id>/progress/upload", methods=["GET"])
@login_required
@session_owner_required
def progress_session_upload(id):
    """
    Gets the job_info

    Gets the local files from files_size.txt
    Gets the files_geo from the session (added there in another function)
    Compares them for discrepancies
    """

    _session = UploadSessionModel.get_by_id(id)
    if _session is None:
        flash(f"Session with ID {id} not found", "error")
        return redirect(url_for("main.dashboard"))

    job_service = JobService()
    sample_service = SampleService()
    file_service = FileService()
    sample_parser_service = SampleParserService()

    job_info = job_service.get_job_info(_session.upload_job_id)
    status_class = STATUS_CLASS.get(job_info["status"]) if job_info else False

    # gather local files
    upload_samples_path = file_service.get_session_folderpath(
        _session.session_title, "upload_samples.ini"
    )
    local_samples = sample_parser_service.get_samples_from_ini(upload_samples_path)

    # gather geo files
    files_geo = SessionCacheService.get_progress_files_geo()

    discrepancies = (
        sample_service.compare_sample_geo(local_samples, files_geo) if files_geo else []
    )
    # format the bytes
    files_geo = (
        [[file[0], int(file[1]), file[2]] for file in files_geo] if files_geo else []
    )

    retrieveGEOForm = SessionRetrieveGEOForm()
    deleteGEOForm = SessionDeleteGEOForm()
    reuploadGEOForm = SessionReuploadGEOForm()
    # todo, why does the submit send to retrieve_geo, who then sends back here?
    # why not treat the form here

    return render_template(
        "progress/upload_progress.html",
        job_info=job_info,
        name=_session.session_title,
        session_id=id,
        retrieveGEOForm=retrieveGEOForm,
        deleteGEOForm=deleteGEOForm,
        reuploadGEOForm=reuploadGEOForm,
        discrepancies=discrepancies,
        status_class=status_class,
        local_samples=local_samples,
        files_geo=files_geo,
    )


@progress.route("/sessions/<id>/finish/upload", methods=["POST"])
def finish_upload(id):
    """
    Sends an email to the user
    """
    # todo, post but no check for csrf, because it is called from the slurm job.....
    # also can be url spammed

    # We suppose the user won't be logged in at the specific time of job finish, so no login required
    # Manual typing of the url can trigger this thing.
    # We cannot verify that the job is actually Completed, because the job is running when it sends the request
    # we just suppose that the upload is done by the point that it sends the notification to this route
    _session = UploadSessionModel.get_by_id(id)
    if _session is None:
        flash(f"Session with ID {id} not found", "error")
        return jsonify({"success": False})

    email_service = EmailService()

    db.session.commit()

    subject = (
        f"Upload to GEO of {_session.session_title} is finished, go finish your upload!"
    )
    # session_user = Users.get_by_id(_session.users_id)
    body = (
        f"Dear {_session.user.name},\n\n"
        f'Your upload session named "{_session.session_title}" is finished.'
        f"Please finish completing the metadata spread sheet if stil not done.\n\n "
        f"To finalize your upload go to https://submit.ncbi.nlm.nih.gov/geo/submission/meta/ "
        f"to upload the completed metadata.\n\n"
        f"Do not hesitate to ask for help!\n"
        f"Sincerely\n"
        f"GeoUploader"
    )
    email_service.send_email(subject, _session.user.email, body)

    return jsonify({"success": True})


@progress.route("/sessions/<id>/finish/md5", methods=["POST"])
def finish_md5(id):
    """
    autocompletes the metadata sheet with the 'md5sheet.tsv' data
    """
    _session = UploadSessionModel.get_by_id(id)
    if _session is None:
        flash(f"Session with ID {id} not found", "error")
        return jsonify({"success": False})

    excel_service = ExcelService()
    file_service = FileService()
    # todo, post but no check for csrf because the request is called from the server.
    #  manual url typing can lead to completion of md5 metadata

    # autocomplete md5checksum
    wb_md5, sheet_md5 = excel_service.prepare_open_metadata(
        _session.session_title, "MD5 Checksums"
    )
    md5tsv = file_service.get_session_folderpath(_session.session_title, "md5sheet.tsv")

    ExcelService.autocomplete_md5checksums(md5tsv, sheet_md5)
    excel_service.prepare_close_metadata(wb_md5, _session.session_title)

    _session.md5_job_finished = True
    db.session.commit()

    return jsonify({"success": True})
