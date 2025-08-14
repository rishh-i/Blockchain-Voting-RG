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


@voting_bp.route("/election/<int:election_id>")
@login_required
def voting_page(election_id):
    election = Election.query.get_or_404(election_id)
    now = datetime.now(timezone.utc)

    # general checks for election status
    if election.start_date > now:
        flash("This election has not started yet.", "error")
        return redirect(url_for("voting.dashboard"))
    if election.end_date and election.end_date < now:
        flash("This election has ended.", "error")
        return redirect(url_for("voting.dashboard"))

    #checks if user has already voted in this election
    existing_vote = VoteRecord.query.filter_by(
        voter_id=current_user.voter_id,
        election_id=election.id
    ).first()
    if existing_vote:
        flash("You have already voted in this election.", "error")
        return redirect(url_for("voting.dashboard"))

    candidates = Candidate.query.filter_by(
        election_id=election.id
    ).all()

    return render_template("vote.html", election = election, candidates = candidates)


@voting_bp.route("/submit_vote", methods=["POST"])
@login_required
# some steps are repeated throughout the routes e.g. checking if user has already voted
def submit_vote():
    election_id = request.form.get("election_id", type=int)
    candidate_id = request.form.getlist("candidate_id", type=int)

    if not election_id or not candidate_id:
        flash("Invalid submission.", "error")
        return redirect(url_for("voting.dashboard"))

    election = Election.query.get_or_404(election_id)
    candidate = Candidate.query.filter_by(
        id=candidate_id,
        election_id=election.id
    ).first()

    if not candidate:
        flash("Invalid candidate selection.", "error")
        return redirect(url_for("voting.voting_page", election_id=election_id))

    existing_vote = VoteRecord.query.filter_by(
        voter_id=current_user.voter_id,
        election_id=election.id
    ).first()

    if existing_vote:
        flash("You have already voted in this election.", "error")
        return redirect(url_for("voting.dashboard"))

    # will use blockchain logic imported from folder blockchain_logic to cast vote
    try:
        bc_vote = Vote(
            voter_id=current_user.voter_id,
            election_id=election.id,
            candidate_id=candidate.id
        )

        current_app.blockchain.add_vote(bc_vote) #adds vote to blockchain

        vote_record = VoteRecord(
            voter_id=current_user.voter_id,
            election_id=election.id
        )
        db.session.add(vote_record)  # adds vote to database
        db.session.commit()

        flash(f"Vote submitted for {candidate.name}", "success")

    except ValueError as e:
        flash(f"Vote submission failed: {str(e)}", "error")
        return redirect(url_for("voting.voting_page", election_id=election_id))

    except Exception as e:
        db.session.rollback()
        flash("An error occurred while submitting your vote", "error")
        return redirect(url_for("voting.voting_page", election_id=election_id))

    return redirect(url_for("voting.dashboard"))





