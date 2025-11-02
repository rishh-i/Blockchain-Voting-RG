from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.election import Election
from models.candidate import Candidate
from models.vote_record import VoteRecord
from blockchain_logic.vote import Vote
from database import db
from datetime import datetime, timezone
import json

voting_bp = Blueprint("voting", __name__)

@voting_bp.route("/dashboard")
@login_required
def dashboard():
    # need to convert sqlalchemy to SQL queries
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

    election_start = election.start_date
    if election_start.tzinfo is None:
        election_start = election_start.replace(tzinfo=timezone.utc)

    election_end = election.end_date
    if election_end and election_end.tzinfo is None:
        election_end = election_end.replace(tzinfo=timezone.utc)

    # general checks for election status
    if election_start > now:
        flash("This election has not started yet.", "error")
        return redirect(url_for("voting.dashboard"))
    if election_end and election_end < now:
        flash("This election has ended.", "error")
        return redirect(url_for("voting.dashboard"))

    #checks if user has already voted in this election
    existing_vote = VoteRecord.query.filter_by(
        voter_id=current_user.voter_id,
        election_id=election_id
    ).first()
    if existing_vote:
        flash("You have already voted in this election.", "error")
        return redirect(url_for("voting.dashboard"))

    candidates = Candidate.query.filter_by(
        election_id=election_id
    ).all()

    return render_template("vote.html", election = election, candidates = candidates)


@voting_bp.route("/submit_vote", methods=["POST"])
@login_required
def submit_vote():
    election_id = request.form.get("election_id", type=int)
    candidate_id = request.form.get("candidate_id", type=int)

    if not election_id or not candidate_id:
        flash("Invalid submission.", "error")
        return redirect(url_for("voting.dashboard"))

    election = Election.query.get_or_404(election_id)
    candidate = Candidate.query.filter_by(
        id=candidate_id,
        election_id=election_id
    ).first()

    if not candidate:
        flash("Invalid candidate selection.", "error")
        return redirect(url_for("voting.voting_page", election_id=election_id))

    existing_vote = VoteRecord.query.filter_by(
        voter_id=current_user.voter_id,
        election_id=election_id
    ).first()

    if existing_vote:
        flash("You have already voted in this election.", "error")
        return redirect(url_for("voting.dashboard"))

    # uses blockchain.py imported from folder blockchain_logic to cast vote
    try:
        print("DEBUG: Creating blockchain vote")
        bc_vote = Vote(
            voter_id=current_user.voter_id,
            election_id=election_id,
            candidate_id=candidate_id
        )
        print(f"DEBUG: Blockchain vote created - valid: {bc_vote.is_valid()}")

        print("DEBUG: Adding vote to blockchain")
        current_app.blockchain.add_vote(bc_vote) #adds vote to blockchain
        print("DEBUG: Vote successfully added to blockchain")

        print("DEBUG: Creating vote record")
        vote_record = VoteRecord(
            voter_id=current_user.voter_id,
            election_id=election_id
        )
        db.session.add(vote_record)  # adds vote to database
        db.session.commit()
        print("DEBUG: Vote record created successfully")

        flash(f"Vote submitted for {candidate.name}", "success")

    except ValueError as e:
        print(f"DEBUG: ValueError occured: {str(e)}")
        flash(f"Vote submission failed: {str(e)}", "error")
        return redirect(url_for("voting.voting_page", election_id=election_id))

    except Exception as e:
        print(f"DEBUG: Exception occured: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        db.session.rollback()
        flash("An error occurred while submitting your vote", "error")
        return redirect(url_for("voting.voting_page", election_id=election_id))

    return redirect(url_for("voting.dashboard"))

def vote_key(item):
    # this function is defined for sorting results, it is called in the results route
    #could also be removed by using lambda function in sort call
    return item["votes"]

@voting_bp.route("/results/<int:election_id>")
@login_required
def results(election_id):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(
        election_id=election_id
    ).all()

    blockchain_results = current_app.blockchain.get_results()
    election_results = blockchain_results.get(election_id, {})

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

    results_data.sort(key=vote_key, reverse=True) # referencing to vote_key function defined above

    return render_template(
        "results.html",
        election=election,
        results=results_data,
        total_votes=total_votes
    )

#admin routes below:

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
            candidate = Candidate(name=name, party=party, election_id=election_id)
            db.session.add(candidate)
            db.session.commit()
            flash(f"Candidate {name} added successfully.", "success")
            return redirect(url_for("voting.admin_elections"))

        except Exception as e:
            db.session.rollback()
            flash("Error adding candidate", "error")

    return render_template("add_candidate.html", election=election)

@voting_bp.route("/debug/blockchain")
@login_required
def debug_blockchain():
    # this route is a debugging tool for the admin (possibly remove later)
    # shows blockchain data (the blockchain.json file)
    if not current_user.is_admin:
        return "Admin only", 403

    blockchain = current_app.blockchain

    debug_info = {
        "chain_length": len(blockchain.chain),
        "pending_votes_count": len(blockchain.pending_votes),
        "pending_votes": [],
        "all_blocks_votes": [],
        "results": blockchain.get_results()
    }

    # shows pending votes
    for vote in blockchain.pending_votes:
        debug_info["pending_votes"].append({
            "voter_id": vote.voter_id,
            "election_id": vote.election_id,
            "candidate_id": vote.candidate_id
        })

    # shows all votes in all blocks
    for i, block in enumerate(blockchain.chain):
        block_votes = []
        for vote in block.votes:
            block_votes.append({
                "voter_id": vote.voter_id,
                "election_id": vote.election_id,
                "candidate_id": vote.candidate_id
            })
        debug_info["all_blocks_votes"].append({
            "block_index": i,
            "votes": block_votes
        })

    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"


@voting_bp.route("/admin/force_mine")
@login_required
# this route allows the admin to add any remaining votes to the blockchain in a new block
# this will usually be needed when for example: block size is 5 votes, and there are 2 pending votes
def force_mine():
    if not current_user.is_admin:
        flash("Admin access required", "error")
        return redirect(url_for("voting.dashboard"))

    current_app.blockchain.add_remaining_votes()
    flash("Pending votes added to blockchain", "success")
    return redirect(url_for("voting.admin_elections"))