from database import db
from datetime import datetime, timezone

def get_current_utc():
    return datetime.now(timezone.utc)

class Base(db.Model):
    # This is a base class which other table classes will inherit from
    __abstract__ = True # this indicates that a table should not be created for base

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=get_current_utc, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_current_utc, onupdate=get_current_utc, nullable=False)