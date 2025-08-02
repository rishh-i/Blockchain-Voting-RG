from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.election import Election
from models.candidate import Candidate
from models.vote_record import VoteRecord
from blockchain_logic.vote import Vote
from app import db
from datetime import datetime, timezone

voting_bp = Blueprint("voting", __name__)

@voting_bp.route("/dashboard")
@login_required
def dashboard():

    #gets current elections
    now = datetime.now(timezone.utc) #stores current time which is used to filter elections
    active_elections = Election.query.filter(
        Election.start_date <= now,
        db.or_(Election.end_date.is_(None), Election.end_date >= now)
    ).all()

    #gets all elections that user has voted in
    voted_elections = db.session.query(VoteRecord.election_id).filter_by(
        voter_id = current_user.voter_id
    ).subquery()

    available_elections = Election.query.filter(
        Election.id.notin_(voted_elections),
        Election.start_date <= now,
        db.or_(Election.end_date.is_(None), Election.end_date >= now)
    ).all()

    return render_template("dashboard.html",
                           active_elections = active_elections,
                           available_elections = available_elections,
                           is_admin = current_user.is_admin,)


