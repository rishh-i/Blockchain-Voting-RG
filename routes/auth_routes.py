from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from database import db
from flask_mail import Message
from models.otp_verification import OTPVerification
import secrets
from datetime import datetime, timedelta, timezone

auth_bp = Blueprint("auth", __name__)

# helper function to generate six digit otp
def generate_otp():
    return str(secrets.randbelow(900000) + 100000)

# helper function to send otp email
def send_otp_email(email, otp_code):
    from app import mail # this imports mail instance from app

    msg = Message(subject="Login Verification Code",
                  recipients=[email],
                  body= f"""
Hello,

Your one time verification code is: {otp_code}

This code will expire in 5 minutes.

Best regards,
Systems @ Rishi Gupta
""")

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated: # if user is already logged in, redirect to dashboard
        return redirect(url_for("voting.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password: #validates against null inputs
            flash("Please fill in all fields.", "error")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first() #sql query to find user by inputted email address

        if user and user.check_password(password):

            # currently removes 2fa for admin but can be easily added back
            if user.is_admin:
                login_user(user)
                flash("Login successful.", "success")
                return redirect(url_for("voting.dashboard"))

            # delete old otps and generate new
            OTPVerification.cleanup_old_otps()
            otp_code = generate_otp()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

            # save otp to database
            otp_record = OTPVerification(
                email=email,
                otp_code=otp_code,
                expires_at=expires_at
            )
            db.session.add(otp_record)
            db.session.commit()

            # send otp email
            if send_otp_email(email, otp_code):
                session["pending_login_email"] = email
                flash("Verification code sent to your email. Please check your inbox.", "success")
                return redirect(url_for("auth.verify_otp"))
            else:
                flash("Failed to send verification code. Please try again.", "error")
                return render_template("login.html")
        else:
            flash("Invalid credentials.", "error")

        return render_template("login.html")

    return render_template("login.html")

@auth_bp.route("/verify-otp", methods=["GET"])
def verify_otp():
    if "pending_login_email" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("auth.login"))

    email = session["pending_login_email"]
    # shows partial email for security
    masked_email = email[:2] + "***@" + email.split('@')[1] if '@' in email else email

    return render_template("verify_otp.html", masked_email=masked_email)

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp_post():
    if "pending_login_email" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("auth.login"))

    email = session["pending_login_email"]
    entered_otp = request.form.get("otp_code", "").strip()

    if not entered_otp:
        flash("Please enter the verification code.", "error")
        return redirect(url_for("auth.verify_otp"))

    # finds the most recent otp record for the email
    otp_record = OTPVerification.query.filter_by(
        email=email,
        is_verified=False
    ).order_by(OTPVerification.created_at.desc()).first()

    if not otp_record:
        flash("Please request a new verification code.", "error")
        return redirect(url_for("auth.login"))

    if otp_record.is_expired():
        flash("Verification code has expired. Please request a new one.", "error")
        return redirect(url_for("auth.login"))

    if otp_record.otp_code == entered_otp:
        otp_record.is_verified = True
        db.session.commit()

        # now user will log in
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user)
            session.pop("pending_login_email", None) # removes pending login email from session
            flash("Login successful.", "success")
            return redirect(url_for("voting.dashboard"))
        else:
            flash("User not found.", "error")
            return redirect(url_for("auth.login"))
    else:
        flash("Invalid verification code. Try again", "error")
        return redirect(url_for("auth.verify_otp"))

# route to resend otp code
@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    if "pending_login_email" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("auth.login"))

    email = session["pending_login_email"]
    OTPVerification.cleanup_old_otps()
    otp_code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    otp_record = OTPVerification(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.session.add(otp_record)
    db.session.commit()

    if send_otp_email(email, otp_code):
        flash("New verification code sent to your email.", "success")
    else:
        flash("Failed to send verification code. Please try again.", "error")

    return redirect(url_for("auth.verify_otp"))

from models.authorised_voter import AuthorisedVoter

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("voting.dashboard"))

    if request.method == "POST":
        voter_id = request.form.get("voter_id")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # null input validation
        if not voter_id or not password or not confirm_password or not firstname or not lastname or not email:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        # checks if entered voter_id is in authorised_voters table
        authorised_voter = AuthorisedVoter.query.filter_by(voter_id=voter_id).first()
        if not authorised_voter:
            flash("Voter ID is not authorised. Contact admin.", "error")
            return render_template("register.html")

        # checks if (authorised) voter_id has already been registered
        if authorised_voter.is_registered:
            flash("You have already registered. Please login.", "error")
            return render_template("register.html")

        # compares password and confirm password entry
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        # checks password length
        if len(password) < 7:
            flash("Password must have at least 7 characters.", "error")
            return render_template("register.html")

        # checks if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email address already registered.", "error")
            return render_template("register.html")

        # checks if voter_id already exists
        existing_user = User.query.filter_by(voter_id=voter_id).first()
        if existing_user:
            flash("Voter ID already exists.", "error")
            return render_template("register.html")

        new_user = User(voter_id=voter_id, firstname=firstname, lastname=lastname, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            authorised_voter.is_registered = True # updates authorised_voter record as registered (bool)
            db.session.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")

        return render_template("register.html")

    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))

