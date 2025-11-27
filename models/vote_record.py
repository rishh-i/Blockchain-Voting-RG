from database import db
from datetime import datetime, timezone
from models.base import Base, get_current_utc

"""
This database table does not store the actual vote that is in the blockchain.
It stores the voter ID and election ID for each vote cast.
This is used to prevent double voting.
"""

class VoteRecord(Base):
    __tablename__ = "vote_records"

    # the primary key is inherited from Base
    voter_id = db.Column(db.String(50), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=get_current_utc, nullable=False)

    election = db.relationship("Election")

    def __repr__(self):
        return f"<VoteRecord {self.voter_id} in Election {self.election_id}>"