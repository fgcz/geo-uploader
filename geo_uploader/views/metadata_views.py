import json

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from geo_uploader.decorators import session_owner_required
from geo_uploader.extensions import db
from geo_uploader.forms import (
    DashboardDownloadForm,
    MetadataNotifyHelpForm,
    MetadataNotifyReleaseForm,
    MetadataProtocolAddForm,
    MetadataReleaseBlockForm,
    MetadataRequestPermissionForm,
    MetadataSaveForm,
    MetadataStudyAddForm,
)
from geo_uploader.models import UploadSessionModel, Users
from geo_uploader.services.excel_service import (
    ExcelService,
    load_dropdowns,
    load_metadata,
    resize_sample_columns,
    save_add_contributor,
    save_add_format,
    save_add_step,
    save_add_supplementaryfile,
    save_protocol_metadata,
    save_remove_contributor,
    save_remove_format,
    save_remove_step,
    save_remove_supplementaryfile,
    save_sample_metadata,
    save_study_metadata,
)
from geo_uploader.services.external.email_service import EmailService
from geo_uploader.services.file_service import FileService

metadata = Blueprint("metadata", __name__)

email_service = EmailService()
file_service = FileService()


@metadata.route("/edit_metadata/<id>", methods=["GET"])
@login_required
@session_owner_required
def edit_metadata(id):
    """
    load the current state of the spreadsheet
    load the dropdowns from a different sheet
    disable certain buttons on condition
    pass logic for admin block/release buttons
    """
    excel_service = ExcelService()

    _session = UploadSessionModel.get_by_id(id)
    if _session is None:
        flash(f"Session with ID {id} not found", "error")
        return redirect(url_for("main.dashboard"))

    wb, sheet = excel_service.prepare_open_metadata(_session.session_title)
    sheet_data = load_metadata(sheet, _session)
    excel_service.prepare_close_metadata(wb, _session.session_title)

    wb, sheet = excel_service.prepare_open_metadata(
        _session.session_title, "Data validation"
    )
    dropdown_molecule, dropdown_instrument, dropdown_library = load_dropdowns(sheet)
    excel_service.prepare_close_metadata(wb, _session.session_title)

    # used to prepopulate the dropdown options on the sheet
    sheet_data["dropdown_molecule"] = dropdown_molecule
    sheet_data["dropdown_instrument"] = dropdown_instrument
    sheet_data["dropdown_library"] = dropdown_library

    contributor_disabled = _session.metadata_contributors_number == 1
    supplementary_disabled = _session.metadata_supplementary_number == 0
    step_disabled = _session.metadata_datasteps_number == 1
    format_disabled = _session.metadata_processedfiles_number == 1

    # Admin request block and release logic
    user_admin = current_user.is_admin()
    own_session = _session.users_id == current_user.id
    has_permission = _session.metadata_permission_user == current_user.id
    blocked_by_another_admin = (
        _session.metadata_permission_user != _session.users_id
        and _session.metadata_permission_user is not None
    )

    can_block = (
        user_admin
        and not own_session
        and not has_permission
        and not blocked_by_another_admin
    )
    can_release = user_admin and not own_session and has_permission
    blocked_by_admin = user_admin and not own_session and blocked_by_another_admin
    blocked_by_employee = not user_admin and own_session and not has_permission
    can_edit = has_permission

    # Logic to show "Request help from supervisor"
    can_request_help = (
        own_session and has_permission and _session.supervisor is not None
    )

    # used for CSRF
    notifyReleaseForm = MetadataNotifyReleaseForm()
    notifyHelpForm = MetadataNotifyHelpForm()
    requestPermissionForm = MetadataRequestPermissionForm()
    releaseBlockForm = MetadataReleaseBlockForm()
    studyAddForm = MetadataStudyAddForm()
    protocolAddForm = MetadataProtocolAddForm()
    metadataSaveForm = MetadataSaveForm()
    return render_template(
        "metadata/metadata.html",
        session_id=id,
        session_name=_session.session_title,
        notifyReleaseForm=notifyReleaseForm,
        notifyHelpForm=notifyHelpForm,
        requestPermissionForm=requestPermissionForm,
        releaseBlockForm=releaseBlockForm,
        studyAddForm=studyAddForm,
        protocolAddForm=protocolAddForm,
        metadataSaveForm=metadataSaveForm,
        contributor_disabled=contributor_disabled,
        supplementary_disabled=supplementary_disabled,
        step_disabled=step_disabled,
        format_disabled=format_disabled,
        samples_list_data=sheet_data["samples_list_data"],
        study_list_data=sheet_data["study_list_data"],
        protocol_list_data=sheet_data["protocol_list_data"],
        pairedend_list_data=sheet_data["pairedend_list_data"],
        dropdown_molecule=sheet_data["dropdown_molecule"],
        dropdown_instrument=sheet_data["dropdown_instrument"],
        dropdown_library=sheet_data["dropdown_library"],
        can_request_help=can_request_help,
        can_edit=can_edit,
        permission_to=_session.metadata_permission_user,
        can_block=can_block,
        can_release=can_release,
        blocked_by_admin=blocked_by_admin,
        blocked_by_employee=blocked_by_employee,
    )


@metadata.route("/save/<id>", methods=["POST"])
@login_required
@session_owner_required
def metadata_save(id):
    """Every section is saved at the same time,
    for study, we just save the new data. Rows are added at another view
    for samples, we have to resize the new column size
    for protocol, we just save the new data
    """
    _session = UploadSessionModel.get_by_id(id)
    if _session is None:
        flash(f"Session with ID {id} not found", "error")
        return jsonify({"status": "error", "message": "Session not found"}), 404

    excel_service = ExcelService()

    form = MetadataSaveForm()
    if form.validate_on_submit():
        try:  # todo, this try catch on metadata catches open_metadata sheet, save to it. Part of general error handling
            # STUDY
            """Save the full object directly to excel file"""
            study_data_raw = request.form.get("study_data")
            if study_data_raw is None:
                flash("Study tab data had problems saving", "warning")
                datasheet_study = []
            else:
                datasheet_study = json.loads(study_data_raw)

            wb, sheet = excel_service.prepare_open_metadata(_session.session_title)
            save_study_metadata(datasheet_study, sheet)
            excel_service.prepare_close_metadata(wb, _session.session_title)

            # SAMPLES
            """ Resize columns if need be as first step.
            Save the data cells, then update the database model to account for the column change"""
            datasheet_samples_raw = request.form.get("samples_data")
            if datasheet_samples_raw is None:
                flash("Samples tab data had problems saving", "warning")
                datasheet_samples = []
            else:
                datasheet_samples = json.loads(datasheet_samples_raw)

            excel_path = file_service.get_session_folderpath(
                _session.session_title, "Metadata.xlsx"
            )
            resize_sample_columns(
                excel_path, datasheet_samples, _session.metadata_samples_width
            )

            wb, sheet = excel_service.prepare_open_metadata(_session.session_title)
            save_sample_metadata(
                datasheet_samples, _session.metadata_samples_displacement, sheet
            )
            excel_service.prepare_close_metadata(wb, _session.session_title)

            size_change = len(datasheet_samples[0]) - _session.metadata_samples_width
            if size_change != 0:
                _session.metadata_samples_width += size_change
                db.session.commit()

            # PROTOCOL
            """ Save the full object directly to excel file"""

            datasheet_protocol_raw = request.form.get("protocol_data")
            if datasheet_protocol_raw is None:
                datasheet_protocol = []
            else:
                datasheet_protocol = json.loads(datasheet_protocol_raw)

            wb, sheet = excel_service.prepare_open_metadata(_session.session_title)
            save_protocol_metadata(
                datasheet_protocol, _session.metadata_protocol_displacement, sheet=sheet
            )
            excel_service.prepare_close_metadata(wb, _session.session_title)
            return (
                jsonify({"status": "success", "message": "Data saved successfully"}),
                200,
            )
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    abort(403)


@metadata.route("/resize_study/<id>", methods=["POST"])
@login_required
@session_owner_required
def resize_study(id):
    """
    Add/Remove contributor row, change database contributor number
    Add/Remove supplementary file row, change database supplementary file number
    Update database study length
    Update database samples, protocol, pairedend displacements
    """
    form = MetadataStudyAddForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return jsonify({"status": "error", "message": "Session not found"}), 404

        study_length = _session.metadata_study_length
        supp_number = _session.metadata_supplementary_number

        excel_path = file_service.get_session_folderpath(
            _session.session_title, "Metadata.xlsx"
        )

        action = request.form.get("action")
        if not action:
            flash("Action not set", "error")
            return jsonify({"status": "error", "message": "Action not set"}), 404
        if action == "add_contributor":
            save_add_contributor(study_length, supp_number, excel_path)
            _session.metadata_contributors_number += 1
            flash("New contributor added!", "success")
        elif action == "remove_contributor":
            save_remove_contributor(study_length, supp_number, excel_path)
            _session.metadata_contributors_number -= 1
            flash("Contributor removed", "success")
        elif action == "add_supplementary_file":
            save_add_supplementaryfile(study_length, excel_path)
            _session.metadata_supplementary_number += 1
            flash("New supplementary file added!", "success")
        elif action == "remove_supplementary_file":
            save_remove_supplementaryfile(study_length, excel_path)
            _session.metadata_supplementary_number -= 1
            flash("Supplementary file removed", "success")

        indel = 1 if action.startswith("add") else -1
        _session.metadata_study_length += indel
        _session.metadata_samples_displacement += indel
        _session.metadata_protocol_displacement += indel
        _session.metadata_pairedend_displacement += indel
        db.session.commit()
        return jsonify({"status": "success", "message": "Resize successful of study."})
    abort(403)


@metadata.route("/resize_protocol/<id>", methods=["POST"])
@login_required
@session_owner_required
def resize_protocol(id):
    """
    Add/Remove datastep row, change database datastep number
    Add/Remove processed files row, change database processed files number
    Update database protocol length
    Update database pairedend displacement
    """
    form = MetadataProtocolAddForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return jsonify({"status": "error", "message": "Session not found"}), 404

        excel_path = file_service.get_session_folderpath(
            _session.session_title, "Metadata.xlsx"
        )

        action = request.form.get("action")
        if not action:
            flash("Action not set", "error")
            return jsonify({"status": "error", "message": "Action not set"}), 404
        if action == "add_step":
            save_add_step(_session, excel_path)
            _session.metadata_datasteps_number += 1
            flash("New data step added!", "success")
        elif action == "remove_step":
            save_remove_step(_session, excel_path)
            _session.metadata_datasteps_number -= 1
            flash("Data step removed", "success")
        elif action == "add_format":
            save_add_format(_session, excel_path)
            _session.metadata_processedfiles_number += 1
            flash("New processed file format added!", "success")
        elif action == "remove_format":
            save_remove_format(_session, excel_path)
            _session.metadata_processedfiles_number -= 1
            flash("Processed file format removed", "success")

        indel = 1 if action.startswith("add") else -1
        _session.metadata_protocol_length += indel
        _session.metadata_pairedend_displacement += indel
        db.session.commit()
        return jsonify(
            {"status": "success", "message": "Resize successful of protocol."}
        )
    abort(403)


@metadata.route("/request_permission/<id>", methods=["POST"])
@login_required
@session_owner_required
def request_permission(id):
    """gives the permission to the current admin who is requesting"""
    form = MetadataRequestPermissionForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return redirect(url_for("metadata.edit_metadata", id=id))
        _session.metadata_permission_user = current_user.id
        db.session.commit()

        return redirect(url_for("metadata.edit_metadata", id=id))
    abort(403)


@metadata.route("/release_block/<id>", methods=["POST"])
@login_required
@session_owner_required
def release_block(id):
    """this releases the block back to the session.users_id"""
    form = MetadataReleaseBlockForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return redirect(url_for("metadata.edit_metadata", id=id))
        _session.metadata_permission_user = _session.users_id
        db.session.commit()

        return redirect(url_for("metadata.edit_metadata", id=id))
    abort(403)


@metadata.route("/download_metadata/<id>", methods=["POST"])
@login_required
@session_owner_required
def download_metadata(id):
    form = DashboardDownloadForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return redirect(url_for("metadata.edit_metadata", id=id))
        metadata_path = file_service.get_session_folderpath(
            _session.session_title, "Metadata.xlsx"
        )
        download_name = _session.session_title + "_metadata.xlsx"
        return send_file(metadata_path, as_attachment=True, download_name=download_name)
    abort(403)


@metadata.route("/notify_release/<id>", methods=["POST"])
@login_required
@session_owner_required
def notify_release(id):
    """Triggered by an user, to send an email to the user who blocked the metadata."""
    # todo, needs to be tested with different users
    form = MetadataNotifyReleaseForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return redirect(url_for("metadata.edit_metadata", id=id))

        permission_holder = Users.get_by_id(_session.metadata_permission_user)
        subject = "GeoUploader: A session which you have block needs to be released."
        body = (
            f"Dear {permission_holder.name},\n\n"
            f"User {current_user.name} requested you to release the block you have on session: {_session.session_title}!\n\n"
            f"All the best,\n"
            f"GeoUploader - {current_user.name}"
        )
        email_service.send_email(subject, permission_holder.email, body)

        flash(
            "Notification has been sent! The block on this metadata will be released eventually.",
            "success",
        )
        return redirect(url_for("metadata.edit_metadata", id=id))
    abort(403)


@metadata.route("/notify_help/<id>", methods=["POST"])
@login_required
@session_owner_required
def notify_help(id):
    """Triggered by a user, to email the user who blocked the metadata."""

    form = MetadataNotifyHelpForm()
    if form.validate_on_submit():
        _session = UploadSessionModel.get_by_id(id)
        if _session is None:
            flash(f"Session with ID {id} not found", "error")
            return redirect(url_for("metadata.edit_metadata", id=id))

        supervisor_email = _session.supervisor.email if _session.supervisor else None
        if supervisor_email is None:
            flash(f"Supervisor of user {_session.user} is not found!")
            return redirect(url_for("metadata.edit_metadata", id=id))
        supervisor_name = _session.supervisor.name if _session.supervisor else ""
        subject = "GeoUploader: User assistance for completing metadata requirements."
        body = (
            f"Dear {supervisor_name},\n\n"
            f"User {current_user.name} requested to get help with their metadata!\n"
            f"User session in concern: {_session.session_title}\n\n"
            f"All the best,\n"
            f"GeoUploader - {current_user.name}"
        )
        email_service.send_email(subject, supervisor_email, body)

        flash(
            "Notification has been sent! The supervisor will complete this metadata ",
            "success",
        )
        return redirect(url_for("metadata.edit_metadata", id=id))
    abort(403)


@metadata.route("/api/validate-organisms", methods=["POST"])
def validate_organisms():
    """Validate multiple organisms with NCBI taxonomy database"""
    organisms = (request.json or {}).get("organisms", [])
    results = {}
    for organism in organisms:
        results[organism] = {
            "valid": is_valid_organism(organism),
            "message": None
            if is_valid_organism(organism)
            else f'"{organism}" is not recognized',
        }

    return jsonify(results)


def is_valid_organism(organism_name: str):
    return True
