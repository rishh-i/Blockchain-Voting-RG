from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

from database import db
login_manager = LoginManager()

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), "templates"))

    #debugging statements
    print(f"Template folder: {app.template_folder}")
    print(f"App root path: {app.root_path}")

    #config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///voting.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Log in to access this page."

    # initialises blockchain
    from blockchain_logic.blockchain import Blockchain
    app.blockchain = Blockchain()

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # register blueprints
    from routes.auth_routes import auth_bp
    from routes.voting_routes import voting_bp
    from routes.blockchain_routes import blockchain_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(voting_bp, url_prefix="/voting")
    app.register_blueprint(blockchain_bp, url_prefix="/blockchain")

    # main route
    @app.route("/")
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for("voting.dashboard"))
        return redirect(url_for("auth.login"))

    #create database tables
    with app.app_context():
        # import models before db is created
        from models.user import User
        # ide shows models are not used but they are needed for db creation
        from models.election import Election
        from models.candidate import Candidate
        from models.vote_record import VoteRecord

        db.create_all()
        print("Database tables created.")

        admin = User.query.filter_by(voter_id="admin").first()
        if not admin:
            admin = User(voter_id="admin", is_admin=True)
            admin.set_password("admin123") #have to change later
            db.session.add(admin)
            db.session.commit()
            # this creates an admin user if it doesn't exist already

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)