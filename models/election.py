from database import db
from datetime import datetime, timezone
from models.base import Base, get_current_utc

class Election(Base):
    __tablename__ = "elections"

    #id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, default=get_current_utc)
    end_date = db.Column(db.DateTime, nullable=True)

    candidates = db.relationship("Candidate", back_populates="election", cascade="all, delete-orphan")

    @property
    def start_date_utc(self):
        # converts start_date (and end_date in next function) to UTC if no timezone info
        if self.start_date.tzinfo is None:
            return self.start_date.replace(tzinfo=timezone.utc)
        return self.start_date

    @property
    def end_date_utc(self):
        if self.end_date is None:
            return None
        if self.end_date.tzinfo is None:
            return self.end_date.replace(tzinfo=timezone.utc)
        return self.end_date

    def __repr__(self):
        return f"<Election {self.name}>"