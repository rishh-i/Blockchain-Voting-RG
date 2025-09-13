from database import db
from datetime import datetime, timezone

"""
db model does not store the actual vote as that is in the blockchain.
It is used to prevent double voting.
"""

class VoteRecord(db.Model):
    __tablename__ = "vote_records"

    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    election = db.relationship("Election")
    def __repr__(self):
        return f"<VoteRecord {self.voter_id} in Election {self.election_id}>"