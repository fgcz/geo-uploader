import logging
import secrets

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from geo_uploader.extensions import db
from geo_uploader.forms import LoginForm, RegisterForm, ResendVerificationForm
from geo_uploader.models import USER, Users
from geo_uploader.services.auth_service import AuthResult, AuthService
from geo_uploader.services.session_cache_service import SessionCacheService
from geo_uploader.utils.url_helpers import URLHelper

logger = logging.getLogger(__name__)
auth = Blueprint("auth", __name__)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    SessionCacheService.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("main.index"))


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    SessionCacheService.clear_user_login()
    next_page = request.args.get("next") or request.form.get("next")

    form = LoginForm(login=request.args.get("login", None))

    if form.validate_on_submit():
        username = form.name.data
        password = form.password.data
        if not username or not password:
            flash("username and password are required", "error")
            return render_template("main/login.html", form=form, next=next_page)

        auth_service = AuthService()
        result, user, message = auth_service.authenticate_user(username, password)

        # Validate the auth service response before passing to handler
        if user is None:
            flash("Authentication failed", "error")
            return render_template("main/login.html", form=form, next=next_page)

        # Provide defaults for optional parameters
        safe_message = message or "Authentication completed"
        safe_next_page = next_page or ""

        return _handle_login_result(result, user, safe_message, safe_next_page)
    return render_template("main/login.html", form=form, next=next_page)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Check if user already exists
        existing_user = Users.query.filter(
            (Users.name == username) | (Users.email == email)
        ).first()

        if existing_user:
            if existing_user.name == username:
                flash(
                    "Username already exists. Please choose a different one.", "danger"
                )
            else:
                flash(
                    "Email already registered. Please use a different email or login.",
                    "danger",
                )
            return render_template("auth/register.html", form=form)

        try:
            # Create new user
            user = Users(
                name=username,
                full_name=username,
                email=email,
                role_code=USER,
                is_email_verified=False,
            )
            user.set_password(password)

            # Generate email activation key
            user.email_activation_key = secrets.token_urlsafe(32)

            db.session.add(user)
            db.session.commit()

            # Send verification email
            try:
                from geo_uploader.services.external.email_service import EmailService

                email_service = EmailService()

                verification_url = url_for(
                    "auth.verify_email", token=user.email_activation_key, _external=True
                )

                subject = "GeoUploader: Please verify your email address"
                body = (
                    f"Dear {user.full_name},\n\n"
                    f"Thank you for registering with GeoUploader!\n\n"
                    f"Please click the following link to verify your email address:\n"
                    f"{verification_url}\n\n"
                    f"If you didn't create this account, please ignore this email.\n\n"
                    f"Best regards,\n"
                    f"GeoUploader Team"
                )

                res = email_service.send_email(subject, user.email, body)
                if res != "Email sent!":
                    logger.error(f"Problem sending the email: {res}")
                    flash("Email verification failed. Please try again.", "danger")
                    return render_template("auth/register.html", form=form)

                flash(
                    "Registration successful! Please check your email to verify your account.",
                    "success",
                )
                return redirect(
                    url_for("auth.email_verification_sent", email=user.email)
                )

            except Exception as e:
                logger.error(f"Failed to send verification email to {user.email}: {e}")
                flash(
                    "Registration successful, but we couldn't send the verification email. "
                    "Please contact support.",
                    "warning",
                )
                return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed for user {username}: {e}")
            flash("Registration failed. Please try again.", "danger")
            return render_template("auth/register.html", form=form)

    return render_template("auth/register.html", form=form)


@auth.route("/verify-email/<token>")
def verify_email(token):
    """Verify email address using the activation token"""
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for("main.index"))

    if not token:
        flash("Invalid verification link.", "danger")
        return redirect(url_for("auth.login"))

    user = Users.query.filter_by(email_activation_key=token).first()

    if not user:
        flash("Invalid or expired verification link.", "danger")
        return redirect(url_for("auth.login"))

    if user.is_email_verified:
        flash("Email already verified. You can log in now.", "info")
        return redirect(url_for("auth.login"))

    try:
        user.verify_email()
        db.session.commit()

        flash("Email verified successfully! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Email verification failed for user {user.name}: {e}")
        flash(
            "Email verification failed. Please try again or contact support.", "danger"
        )
        return redirect(url_for("auth.login"))


@auth.route("/email-verification-sent")
def email_verification_sent():
    """Show confirmation page after registration"""
    email = request.args.get("email")
    if not email:
        flash("Invalid request.", "error")
        return redirect(url_for("auth.register"))

    return render_template("auth/email_verification_sent.html", email=email)


@auth.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    """Resend email verification if user didn't receive it"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = ResendVerificationForm()

    if form.validate_on_submit():
        email = form.email.data
        user = Users.query.filter_by(email=email, is_email_verified=False).first()

        if not user:
            flash("No unverified account found with this email address.", "danger")
            return render_template("auth/resend_verification.html", form=form)

        try:
            # Generate new activation key if needed
            if not user.email_activation_key:
                user.email_activation_key = secrets.token_urlsafe(32)
                db.session.commit()

            # Send verification email
            from geo_uploader.services.external.email_service import EmailService

            email_service = EmailService()

            verification_url = url_for(
                "auth.verify_email", token=user.email_activation_key, _external=True
            )

            subject = "GeoUploader: Email verification (Resent)"
            body = (
                f"Dear {user.full_name},\n\n"
                f"Here's your email verification link as requested:\n"
                f"{verification_url}\n\n"
                f"If you didn't request this, please ignore this email.\n\n"
                f"Best regards,\n"
                f"GeoUploader Team"
            )

            res = email_service.send_email(subject, user.email, body)
            if res != "Email sent!":
                logger.error(f"Problem sending the email: {res}")
                flash("Email verification failed. Please try again.", "danger")
                return
            flash("Verification email sent! Please check your inbox.", "success")
            return redirect(url_for("auth.email_verification_sent", email=user.email))

        except Exception as e:
            logger.error(f"Failed to resend verification email to {user.email}: {e}")
            flash(
                "Failed to send verification email. Please try again later.", "danger"
            )

    return render_template("auth/resend_verification.html", form=form)


def _handle_login_result(result: AuthResult, user: Users, message: str, next_page: str):
    if result == AuthResult.INVALID_CREDENTIALS:
        flash("Invalid login credentials", "danger")
        return redirect(url_for("auth.login"))

    elif result == AuthResult.LOGIN_FAILED:
        flash("Login failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    elif result == AuthResult.EMAIL_REQUIRED:
        SessionCacheService.store_user_data(user.name, has_unfinished_profile=True)
        flash("Please complete your profile to finish login", "info")
        return redirect(url_for("main.profile_details"))

    elif result == AuthResult.SUCCESS:
        SessionCacheService.store_user_data(user.name)

        if login_user(user):
            flash("Logged in successfully", "success")
            return redirect(URLHelper.get_safe_redirect_url(next_page))
        else:
            flash("Login failed. Please try again.", "danger")
            return redirect(url_for("auth.login"))

    flash("An unexpected error occurred", "danger")
    return redirect(url_for("auth.login"))
