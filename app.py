from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


# main point to run application

from database import db
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), "templates")) # links to the templates folder which contains html for UI

    # db using sqlalchemy, raw SQL will be added in documentation
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///voting.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # email config for otps
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True") == "True"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME"))

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Log in to access this page."

    # initialises blockchain from blockchain_logic folder
    from blockchain_logic.blockchain import Blockchain

    # assigns JSON file which stores the actual blockchain to the variable
    blockchain_file = os.path.join(os.path.dirname(__file__), "blockchain.json")
    app.blockchain = Blockchain(blockchain_file)


    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # blueprints loaded for the web-app which other pages/sites will build from
    from routes.auth_routes import auth_bp
    from routes.voting_routes import voting_bp
    from routes.blockchain_routes import blockchain_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(voting_bp, url_prefix="/voting")
    app.register_blueprint(blockchain_bp, url_prefix="/blockchain")

    # default route
    @app.route("/")
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for("voting.dashboard"))
        return redirect(url_for("auth.login"))

    #creates database tables
    with app.app_context():
        # import models before db is created
        from models.user import User
        from models.election import Election
        from models.candidate import Candidate
        from models.vote_record import VoteRecord
        from models.authorised_voter import AuthorisedVoter
        from models.otp_verification import OTPVerification
        # ide shows models are not used, but they are needed for db creation

        db.create_all()
        print("Database tables created.")

        # checks if admin account is stored in db
        admin = User.query.filter_by(voter_id="admin").first()
        if not admin:
            # creates an initial admin account if one hasn't been created already i.e. first time executing program
            admin = User(voter_id="admin", is_admin=True, firstname="Admin", lastname="istrator", email="admin@voting.com")
            admin.set_password("admin123") #have to change later
            db.session.add(admin)
            db.session.commit()

        sync_blockchain_with_database(app.blockchain)

    return app

def sync_blockchain_with_database(blockchain):
    # syncs blockchain with db records to ensure consistency on app restart

    try:
        from models.vote_record import VoteRecord

        blockchain_votes = set()
        # this is for the votes already mined/added in the blockchain
        # votes from the blockchain are added to a set
        for block in blockchain.chain:
            for vote in block.votes:
                blockchain_votes.add(f"{vote.voter_id}_{vote.election_id}")

        # this is for the pending votes not yet mined/added in the blockchain
        for vote in blockchain.pending_votes:
            blockchain_votes.add(f"{vote.voter_id}_{vote.election_id}")

        # get all *vote records* from database
        all_vote_records = VoteRecord.query.all()
        db_votes = {f"{vote.voter_id}_{vote.election_id}" for vote in all_vote_records} # set comprehension

        # below are methods to handle errors in the system
        # find the votes that are not in database but are in blockchain
        # this is done by subtracting the sets which leaves the values in bc_votes that are not in db_votes
        votes_to_add = blockchain_votes - db_votes
        if votes_to_add:
            # add the remaining votes to the db
            for vote_key in votes_to_add:
                voter_id, election_id = vote_key.split("_")
                record = VoteRecord(voter_id=voter_id, election_id=int(election_id))
                db.session.add(record)
            db.session.commit()

        # find the votes that are in database but not in blockchain
        votes_in_db_not_in_bc = db_votes - blockchain_votes
        if votes_in_db_not_in_bc:
            # ideally this should not happen, so we log a warning for further review
            print(f"WARNING: Data inconsistency as {len(votes_in_db_not_in_bc)} votes are in database but not in blockchain.")

    except Exception as e:
        print("Error: ", str(e))
        db.session.rollback()

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
