from database import db
from models.base import Base

class Candidate(Base):
    __tablename__ = "candidates"

    #id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(100), nullable=True)
    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)

    election = db.relationship("Election", back_populates="candidates")

    def __repr__(self):
        return f"<Candidate {self.name} from {self.party}>"