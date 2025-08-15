from database import db
from datetime import datetime, timezone

class Election(db.Model):
    __tablename__ = "elections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime, nullable=True)

    candidates = db.relationship("Candidate", back_populates="election", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Election {self.name}>"
