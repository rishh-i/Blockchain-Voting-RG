from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import hashlib

app = Flask(__name__, template_folder='templates')
app.secret_key = "secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voters.db"
db = SQLAlchemy(app)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# sample registered users
registered_voters = {
    "voter1": "abc123",
    "voter2": "def456"
}

def hash_voter_id(voter_id):
    return hashlib.sha256(voter_id.encode()).hexdigest()

@app.route('/')
def index():
    if "voter_id" in session:
        return redirect(url_for("dashboard"))
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
#this method uses the database but is incomplete.
#need to add a registration method to add users to the database
def login():
    if request.method == "POST":
        voter_id = request.form["voter_id"].strip()
        password = request.form["password"]

        user = Voter.query.filter_by(voter_id=voter_id).first()
        if user and user.password == password:
            session["voter_id"] = hash_voter_id(voter_id)
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if "voter_id" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", voter_id=session["voter_id"])

@app.route('/logout')
def logout():
    session.pop("voter_id", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)

