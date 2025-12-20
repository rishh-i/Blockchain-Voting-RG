from database import db
from models.base import Base

class Feedback(Base):
    __tablename__ = "feedback"

    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=True) # e.g. positve, negative, neutral
    sentiment_score = db.Column(db.Float, nullable=True) # confidence score (0,1)

    election = db.relationship("Election")

    def __repr__(self):
        return f"<Feedback for Election {self.election_id}: {self.sentiment}>"