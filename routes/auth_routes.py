from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from database import db

auth_bp = Blueprint("auth", __name__)

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
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for("voting.dashboard"))
        else:
            flash("Invalid credentials.", "error")

        return render_template("login.html")

    return render_template("login.html")

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

