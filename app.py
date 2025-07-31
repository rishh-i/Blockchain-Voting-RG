from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os

from login.loginsys import app

db = SQLAlchemy()
session_manager = Session()

def create_app():
    app = Flask(__name__)

    #secret key for the sessions
    app.config["SECRET_KEY"] = "secret_key"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voting.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_FILE_DIR"] = os.path.join(app.instance_path, "flask_session")

    db.init_app(app)
    session_manager.init_app(app)

    from models.user import User
    from models.election import Election
    from models.vote_record import VoteRecord

    with app.app_context():
        db.create_all()

