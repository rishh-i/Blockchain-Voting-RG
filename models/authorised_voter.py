from database import db
from models.base import Base

class AuthorisedVoter(Base):
    __tablename__ = "authorised_voters"

    voter_id = db.Column(db.String(50), unique=True, nullable=False)
    is_registered = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<AuthorisedVoter {self.voter_id}>"