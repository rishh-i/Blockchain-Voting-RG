from flask import Blueprint, render_template, jsonify, current_app, request, flash, redirect, url_for
from flask_login import login_required, current_user

def handle_different_vote_types_object(vote):
    # currently this is used for adding the correct type of candiadte id info to the vote
    if hasattr(vote, "candidate_id"):
        return {"candidate_id": vote.candidate_id}
    elif hasattr(vote, "ranked_candidate_ids"):
        return {"ranked_candidate_ids": vote.ranked_candidate_ids}
    return {}

def handle_different_vote_types_dict(vote):
    if "candidate_id" in vote:
        return {"candidate_id": vote["candidate_id"]}
    elif "ranked_candidate_ids" in vote:
        return {"ranked_candidate_ids": vote["ranked_candidate_ids"]}
    return {}

blockchain_bp = Blueprint("blockchain", __name__)
@blockchain_bp.route("/explorer")
@login_required
def explorer():
    # displays the blockchain explorer page
    return render_template("blockchain_explorer.html")

@blockchain_bp.route("/api/chain")
@login_required
def get_chain():
    try:
        chain_data = current_app.blockchain.get_blockchain()

        anonymous_chain = []
        for block in chain_data:
            anonymous_block = block.copy()
            anonymous_votes = []
            for vote in block["votes"]:
                anonymous_vote = {
                    "election_id": vote["election_id"],
                    "timestamp": vote["timestamp"],
                    "vote_hash": vote["vote_hash"],
                    "voter_id_hidden": True
                }
                # handles different vote types (can be done by this function or the code commented below)
                candidate_id = handle_different_vote_types_dict(vote)
                anonymous_vote.update(candidate_id)

                anonymous_votes.append(anonymous_vote)
            anonymous_block["votes"] = anonymous_votes
            anonymous_chain.append(anonymous_block)

        return jsonify(
            {
                "chain": anonymous_chain,
                "length": len(chain_data),
                "is_valid": current_app.blockchain.validate_chain(),
                "anonymous_view": True
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route("/api/block/<int:block_index>")
@login_required
def get_block(block_index):
    try:
        chain = current_app.blockchain.chain
        if 0<= block_index < len(chain):
            block = chain[block_index]
            block_data = block.to_dict()

            # if not current_user.is_admin:
            # from lines 55-67, code was in a loop which excluded admins. Now everyone has the normal bc.
            anonymous_votes = []
            for vote in block_data["votes"]:
                anonymous_vote = {
                    "election_id": vote["election_id"],
                    "timestamp": vote["timestamp"],
                    "vote_hash": vote["vote_hash"],
                    "voter_id_hidden": True
                }
                # refer to get_chain for explanation
                candidate_id = handle_different_vote_types_dict(vote)
                anonymous_vote.update(candidate_id)

                anonymous_votes.append(anonymous_vote)
            block_data["votes"] = anonymous_votes
            block_data["anonymous_view"] = True
            return jsonify(block_data)
        else:
            return jsonify({"error": "Block not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@blockchain_bp.route("/api/validate_vote", methods=["POST"])
@login_required
def validate_vote():

    # method to allow user to check if their vote is recorded in the blockchain.
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        voter_id = data.get("voter_id")
        election_id = data.get("election_id")

        if not voter_id or not election_id:
            return jsonify({"error": "Voter ID and Election ID are required"}), 400

        if not current_user.is_admin and voter_id != current_user.voter_id:
            return jsonify({"error": "Unauthorised access"}), 403

        vote_found = False
        vote_details = None

        for block_index, block in enumerate(current_app.blockchain.chain):
            for vote in block.votes:
                if vote.voter_id == voter_id and vote.election_id == election_id:
                    vote_found = True
                    vote_details = {
                        "block_index": block_index,
                        "timestamp": vote.timestamp,
                        "vote_hash": vote.vote_hash,
                        "block_hash": block.hash
                    }

                    # refer to get_chain for explanation
                    candidate_id = handle_different_vote_types_object(vote)
                    vote_details.update(candidate_id)

                    break
            if vote_found:
                break

        #also checks pending votes if not mined into a block yet
        if not vote_found:
            for vote in current_app.blockchain.pending_votes:
                if vote.voter_id == voter_id and vote.election_id == election_id:
                    vote_found = True
                    vote_details = {
                        "block_index": "Pending",
                        "timestamp": vote.timestamp,
                        "vote_hash": vote.vote_hash,
                        "block_hash": "Pending"
                    }

                    # refer to get_chain for explanation
                    candidate_id = handle_different_vote_types_object(vote)
                    vote_details.update(candidate_id)

                    break
        response_data = {"vote_found": vote_found}
        if vote_details:
            response_data.update(vote_details)
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


"""
Below are routes that give more detailed data on the blockcain, mainly showing voter IDs
It can be used in general since voter IDs are random strings but currently the id is hidden
When these routes were used, they were admin routes only

Note: if i want to re-use the routes, html changes need to be made:
- admin_blockchain_explorer.html needs to be re-created (kept a copy)
- minor changes (buttons) on blockchain_explorer.html and dashboard.html
"""

# @blockchain_bp.route("api/admin/full_chain")
# @login_required
# def get_full_chain():
#
#     #only admin account can access full chain with voter details
#     if not current_user.is_admin:
#         return jsonify({"error": "Admin access required"}), 403
#
#     try:
#         chain_data = current_app.blockchain.get_blockchain()
#         return jsonify({
#             "chain": chain_data,
#             "length": len(chain_data),
#             "is_valid": current_app.blockchain.validate_chain(),
#             "admin_view": True
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @blockchain_bp.route("/admin/full_explorer")
# @login_required
# def admin_full_explorer():
#     # this is for the admin page of the bc explorer; i.e. they have greater access and privileges
#     if not current_user.is_admin:
#         flash("Admin access required", "error")
#         return redirect(url_for("voting.dashboard"))
#     return render_template("admin_blockchain_explorer.html")