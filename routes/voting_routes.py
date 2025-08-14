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

@voting_bp.route("/results/<int:election_id>")
@login_required
def results(election_id):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(
        election_id=election.id
    ).all()

    blockchain_results = current_app.blockchain.get_results()
    election_results = blockchain_results.get(election.id, {})

    results_data = []
    total_votes = sum(election_results.values())

    for candidate in candidates:
        vote_count = election_results.get(candidate.id, 0)
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        results_data.append({
            "candidate": candidate,
            "votes": vote_count,
            "percentage": round(percentage, 2)
        })

    results_data.sort(key=lambda x: x["votes"], reverse=True)

    return render_template(
        "results.html",
        election=election,
        results=results_data,
        total_votes=total_votes
    )

#admin routes below

@voting_bp.route("/admin/elections")
@login_required
def admin_elections():
    if not current_user.is_admin:
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("voting.dashboard"))

    elections = Election.query.all()
    return render_template("admin_elections.html", elections=elections)

@voting_bp.route("/admin/create_election", methods=["GET","POST"])
@login_required
def create_election():
    if not current_user.is_admin:
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("voting.dashboard"))

    if request.method == "POST":
        name = request.form.get("name")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        if not name or not start_date_str:
            flash("Please fill in all required fields.", "error")
            return render_template("create_election.html")

        try:
            start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc)
            end_date = None
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone.utc)

            election = Election(name=name, start_date=start_date, end_date=end_date)
            db.session.add(election)
            db.session.commit()
            flash("Election created.", "success")
            return redirect(url_for("voting.admin_elections"))

        except Exception as e:
            db.session.rollback()
            flash("Error creating election", "error")

    return render_template("create_election.html")

@voting_bp.route("/admin/add_candidate/<int:election_id>", methods=["GET", "POST"])
@login_required
def add_candidate(election_id):
    if not current_user.is_admin:
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("voting.dashboard"))

    election = Election.query.get_or_404(election_id)

    if request.method == "POST":
        name = request.form.get("name")
        party = request.form.get("party")

        if not name:
            flash("Please enter a candidate name.", "error")
            return render_template("add_candidate.html", election=election)

        try:
            candidate = Candidate(name=name, party=party, election_id=election.id)
            db.session.add(candidate)
            db.session.commit()
            flash(f"Candidate {name} added successfully.", "success")
            return redirect(url_for("voting.admin_elections"))

        except Exception as e:
            db.session.rollback()
            flash("Error adding candidate", "error")

    return render_template("add_candidate.html", election=election)