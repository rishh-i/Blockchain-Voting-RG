from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from database import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("voting.dashboard"))

    if request.method == "POST":
        voter_id = request.form.get("voter_id")
        password = request.form.get("password")

        if not voter_id or not password:
            flash("Please fill in all fields.", "error")
            return render_template("login.html")

        user = User.query.filter_by(voter_id=voter_id).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for("voting.dashboard"))
        else:
            flash("Invalid credentials.", "error")

        return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("voting.dashboard"))

    if request.method == "POST":
        voter_id = request.form.get("voter_id")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not voter_id or not password or not confirm_password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if len(password) < 7:
            flash("Password must have at least 7 characters.", "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(voter_id=voter_id).first()
        if existing_user:
            flash("Voter ID already exists.", "error")
            return render_template("register.html")

        new_user = User(voter_id=voter_id)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")

        return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))

