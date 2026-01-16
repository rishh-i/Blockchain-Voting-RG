from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.election import Election
from models.candidate import Candidate
from models.vote_record import VoteRecord
#from blockchain_logic.vote import Vote
from blockchain_logic.vote_builder import VoteBuilder
from blockchain_logic.results_calculator import ResultsCalculator
from database import db
from datetime import datetime, timezone
import json

voting_bp = Blueprint("voting", __name__)

@voting_bp.route("/dashboard")
@login_required
def dashboard():

    now = datetime.now(timezone.utc) #stores current time which is used to filter elections

    # gets active elections
    active_elections = Election.query.filter(
        Election.start_date <= now,
        db.or_(Election.end_date.is_(None), Election.end_date >= now)
    ).all()

    # gets past elections
    past_elections = Election.query.filter(
        Election.end_date.isnot(None),
        Election.end_date < now
    ).order_by(Election.end_date.desc()).all()

    #gets all elections that user has voted in
    voted_elections = db.session.query(VoteRecord.election_id).filter_by(
        voter_id = current_user.voter_id
    ).subquery()

    # gets elections that are ongoing but user hasnt voted in yet
    available_elections = Election.query.filter(
        Election.id.notin_(voted_elections),
        Election.start_date <= now,
        db.or_(Election.end_date.is_(None), Election.end_date >= now)
    ).all()

    return render_template("dashboard.html",
                           active_elections = active_elections,
                           past_elections = past_elections,
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

    if election.is_ranked_choice():
        return render_template("vote_ranked.html", election = election, candidates = candidates)
    else:
        return render_template("vote.html", election = election, candidates = candidates)


@voting_bp.route("/submit_vote", methods=["POST"])
@login_required
def submit_vote():
    election_id = request.form.get("election_id", type=int)

    if not election_id:
        flash("Invalid submission.", "error")
        return redirect(url_for("voting.dashboard"))

    election = Election.query.get_or_404(election_id)

    existing_vote = VoteRecord.query.filter_by(
        voter_id=current_user.voter_id,
        election_id=election_id
    ).first()

    if existing_vote:
        flash("You have already voted in this election.", "error")
        return redirect(url_for("voting.dashboard"))

    try:
        if election.is_standard_choice():
            # standard vote processing
            candidate_id = request.form.get("candidate_id", type=int)

            if not candidate_id:
                flash("Invalid submission.", "error")
                return redirect(url_for("voting.dashboard"))

            bc_vote = VoteBuilder.create_vote(
                vote_type="standard",
                voter_id=current_user.voter_id,
                election_id=election_id,
                vote_data=candidate_id
            )

        elif election.is_ranked_choice():
            # ranked vote processing
            ranked_candidates = []
            max_rank = len(election.candidates)

            for rank in range(1, max_rank + 1):
                candidate_id = request.form.get(f"ranked_{rank}", type=int)
                if candidate_id:
                    ranked_candidates.append(candidate_id)

            if not ranked_candidates:
                flash("You must rank at least one candidate.", "error")
                return redirect(url_for("voting.voting_page", election_id=election_id))

            # validate all candidates exist in this election
            candidate_ids = {c.id for c in election.candidates}
            if not all(cid in candidate_ids for cid in ranked_candidates):
                flash("Invalid candidate selection.", "error")
                return redirect(url_for("voting.voting_page", election_id=election_id))

            bc_vote = VoteBuilder.create_vote(
                vote_type="ranked",
                voter_id=current_user.voter_id,
                election_id=election_id,
                vote_data=ranked_candidates
            )

        else:
            flash("Unkown election type.", "error")
            return redirect(url_for("voting.dashboard"))

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

        flash(f"Vote submitted", "success")

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
    # this could also be replaced by using lambda function in sort call
    return item["votes"]


@voting_bp.route("/results/<int:election_id>")
@login_required
def results(election_id):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(
        election_id=election_id
    ).all()

    blockchain_results = current_app.blockchain.get_results()
    election_results = blockchain_results.get(election_id, [])

    calculator = ResultsCalculator.create_calculator(
        vote_type=election.vote_type,
        election_id=election_id,
        votes=election_results,
        candidates=candidates
    )
    calculation_result = calculator.calculate_results()

    if election.is_standard_choice():
        vote_counts = calculation_result["vote_counts"]
        total_votes = sum(vote_counts.values())

        results_data = []
        for candidate in candidates:
            vote_count = vote_counts.get(candidate.id, 0)
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
            total_votes=total_votes,
            winner_data = calculation_result["winner_data"]
        )

    elif election.is_ranked_choice():
        rounds = calculation_result["vote_counts"]["rounds"]
        winner_data = calculation_result["winner_data"]

        return render_template(
            "results_ranked.html",
            election=election,
            candidates=candidates,
            rounds=rounds,
            winner_data=winner_data,
            total_votes=calculation_result["total_votes"]
        )


#admin routes below:

from secrets import token_urlsafe
from models.authorised_voter import AuthorisedVoter

@voting_bp.route("/admin/generate_voter_ids", methods=["GET", "POST"])
@login_required
def generate_voter_ids():
    if not current_user.is_admin:
        flash("Admin access required", "error")
        return redirect(url_for("voting.dashboard"))

    generated_ids = []

    if request.method == "POST":
        count = request.form.get("count", type=int, default=1)

        if count < 1 or count > 100:
            flash("Please generate between 1-100 voter IDs.", "error")
            return render_template("generate_voter_ids.html")

        try:
            for _ in range(count): # underscore used since var not needed
                # generates a unique voter ID using token_urlsafe
                voter_id = f"VOTER-{token_urlsafe(8)}" # parameter is for num of random bytes

                # to ensure ids are unique
                while AuthorisedVoter.query.filter_by(voter_id=voter_id).first():
                    voter_id = f"VOTER-{token_urlsafe(8)}"

                auth_voter = AuthorisedVoter(voter_id=voter_id)
                db.session.add(auth_voter)
                generated_ids.append(voter_id)

            db.session.commit()
            flash(f"Generated {count} voter IDs.", "success")

            all_authorised_voters = AuthorisedVoter.query.order_by(AuthorisedVoter.created_at.desc()).all()
            return render_template("generate_voter_ids.html", generated_ids=generated_ids, all_authorised_voters=all_authorised_voters)

        except Exception as e:
            db.session.rollback()
            flash("Error occured generating IDs", "error")

    # for GET requests
    all_authorised_voters = AuthorisedVoter.query.order_by(AuthorisedVoter.created_at.desc()).all()

    return render_template("generate_voter_ids.html", all_authorised_voters=all_authorised_voters)


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
        vote_type = request.form.get("vote_type", "standard")

        if not name or not start_date_str or not vote_type:
            flash("Please fill in all required fields.", "error")
            return render_template("create_election.html")

        if vote_type not in VoteBuilder.get_supported_vote_types():
            flash("Invalid vote type selected.", "error")
            return render_template("create_election.html")

        try:
            start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc)
            end_date = None
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone.utc)

            election = Election(name=name, start_date=start_date, end_date=end_date, vote_type=vote_type)
            db.session.add(election)
            db.session.commit()
            flash(f"Election created with {vote_type} voting.", "success")
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

        if hasattr(vote, "candidate_id"):
            debug_info["candidate_id"] = vote.candidate_id
        elif hasattr(vote, "ranked_candidate_ids"):
            debug_info["ranked_candidate_ids"] = vote.ranked_candidate_ids

        debug_info["pending_votes"].append(debug_info)

    # shows all votes in all blocks
    for i, block in enumerate(blockchain.chain):
        block_votes = []
        for vote in block.votes:
            vote_info = {
                "voter_id": vote.voter_id,
                "election_id": vote.election_id,
                "vote_type": vote.get_vote_type()
            }
            if hasattr(vote, "candidate_id"):
                vote_info["candidate_id"] = vote.candidate_id
            elif hasattr(vote, "ranked_candidate_ids"):
                vote_info["ranked_candidate_ids"] = vote.ranked_candidate_ids

            block_votes.append(vote_info)

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