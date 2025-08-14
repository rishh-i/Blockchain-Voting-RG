from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required, current_user

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
        return jsonify(
            {
                "chain": chain_data,
                "length": len(chain_data),
                "is_valid": current_app.blockchain.validate_chain()
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
            return jsonify(block.to_dict())
        else:
            return jsonify({"error": "Block not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500