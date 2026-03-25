import pytest
import json
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

def setUpModule():
    patch('builtins.print').start()

def tearDownModule():
    patch.stopall()

@pytest.fixture
def blockchain_file(tmp_path):
    # creates temporary blockchain json file deleted after each test
    return str(tmp_path / "test_blockchain.json")


@pytest.fixture
def app(blockchain_file):
    """
    Configured a Flask test app
    It creates a SQLite database in memory and a temporary blockchain json file for testing
    """
    real_path_join = os.path.join

    def redirect_blockchain_path(*args):
        if args[-1] == "blockchain.json":
            return blockchain_file
        else:
            return real_path_join(*args)

    with patch.dict(os.environ, {
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test_secret_key",
        "MAIL_SERVER": "localhost",
        "MAIL_USERNAME": "test@test.com",
        "MAIL_PASSWORD": "testpass",
    }):
        from app import create_app
        with patch("app.os.path.join", side_effect=redirect_blockchain_path):
            flask_app = create_app()

    flask_app.config["TESTING"] = True
    flask_app.config["MAIL_SUPPRESS_SEND"] = True  # disables email sending during tests
    flask_app.config["SECRET_KEY"] = "test_secret_key"  # ensures session cookies are signed with the same key
    flask_app.config["WTF_CSRF_ENABLED"] = False  # disables CSRF protection during tests
    return flask_app


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield app


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


@pytest.fixture
def admin_client(client, app_ctx):
    """tests client as an admin user"""
    client.post("/auth/login", data={
        "email": "admin@voting.com",
        "password": "admin123"
    }, follow_redirects=True)
    return client


@pytest.fixture
def voter_and_client(client, app_ctx):
    """creates an authorised voter and registers them"""
    from database import db
    from models.authorised_voter import AuthorisedVoter

    voter_id = "VOTER-TEST-001"
    db.session.add(AuthorisedVoter(voter_id=voter_id))
    db.session.commit()

    client.post("/auth/register", data={
        "voter_id": voter_id,
        "firstname": "Test",
        "lastname": "Voter",
        "email": "testvoter@example.com",
        "password": "678voting",
        "confirm_password": "678voting",
    }, follow_redirects=True)
    return voter_id, client


@pytest.fixture
def logged_in_voter(voter_and_client, app_ctx):
    voter_id, client = voter_and_client

    with patch("routes.auth_routes.send_otp_email", return_value=True):
        client.post("/auth/login", data={
            "email": "testvoter@example.com",
            "password": "678voting"
        }, follow_redirects=True)

    from database import db
    from models.otp_verification import OTPVerification
    otp_record = OTPVerification.query.filter_by(
        email="testvoter@example.com",
        is_verified=False
    ).first()

    client.post("/auth/verify-otp", data={
        "otp_code": otp_record.otp_code
    }, follow_redirects=True)

    return voter_id, client


@pytest.fixture
def standard_election(app_ctx):
    """standard election with three candidates"""
    from database import db
    from models.election import Election
    from models.candidate import Candidate

    now = datetime.now(timezone.utc)
    election = Election(
        name="Test Standard Election",
        start_date=now - timedelta(hours=1),
        end_date=now + timedelta(hours=23),
        vote_type="standard"
    )
    db.session.add(election)
    db.session.flush()
    for name, party in [("Auxillary", "Party A"), ("Bartholomew", "Party B"), ("Cantilope", "Party C")]:
        db.session.add(Candidate(name=name, party=party, election_id=election.id))
    db.session.commit()
    return election


@pytest.fixture
def ranked_election(app_ctx):
    """ranked choice election with three candidates."""
    from database import db
    from models.election import Election
    from models.candidate import Candidate

    now = datetime.now(timezone.utc)
    election = Election(
        name="Test Ranked Election",
        start_date=now - timedelta(hours=1),
        end_date=now + timedelta(hours=23),
        vote_type="ranked"
    )
    db.session.add(election)
    db.session.flush()
    for name, party in [("Auxillary", "Party A"), ("Bartholomew", "Party B"), ("Cantilope", "Party C")]:
        db.session.add(Candidate(name=name, party=party, election_id=election.id))
    db.session.commit()
    return election


class TestStandardVoting:
    """tests the standard voting flow"""

    def test_standard_vote_recorded_in_blockchain(self, logged_in_voter, standard_election, app_ctx):
        from models.vote_record import VoteRecord
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        response = client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        assert response.status_code == 200

        # database check
        record = VoteRecord.query.filter_by(
            voter_id=voter_id,
            election_id=standard_election.id
        ).first()
        assert record is not None

        # blockchain check
        blockchain_results = app_ctx.blockchain.get_results()
        election_votes = blockchain_results.get(standard_election.id, [])
        voter_votes = [v for v in election_votes if v.voter_id == voter_id]
        assert len(voter_votes) == 1
        assert voter_votes[0].candidate_id == candidate.id

    def test_double_voting_prevented(self, logged_in_voter, standard_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        # first vote should be valid
        client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        # second (duplicate) vote should be rejected
        response = client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        assert b"already voted" in response.data.lower()

        # to confirm only one vote is recorded in the blockchain
        blockchain_results = app_ctx.blockchain.get_results()
        election_votes = blockchain_results.get(standard_election.id, [])
        voter_votes = [v for v in election_votes if v.voter_id == voter_id]
        assert len(voter_votes) == 1

    def test_vote_hash_integrity(self, logged_in_voter, standard_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        for block in app_ctx.blockchain.chain:
            for vote in block.votes:
                if vote.voter_id == voter_id:
                    assert vote.is_valid(), "hash failed integrity check"


class TestRankedVoting:
    """
    tests the ranked choice voting flow
    extra part for ensuring candidate order is preserved
    """

    def test_ranked_vote_stored_correctly(self, logged_in_voter, ranked_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidates = Candidate.query.filter_by(
            election_id=ranked_election.id).all()
        ranked_order = [c.id for c in candidates]

        form_data = {"election_id": ranked_election.id}
        for i, cid in enumerate(ranked_order, start=1):
            form_data[f"ranked_{i}"] = cid

        response = client.post("/voting/submit_vote",
                               data=form_data,
                               follow_redirects=True)
        assert response.status_code == 200

        # get vote from blockchain and check if order is preserved
        blockchain_results = app_ctx.blockchain.get_results()
        election_votes = blockchain_results.get(ranked_election.id, [])
        voter_votes = [v for v in election_votes if v.voter_id == voter_id]
        assert len(voter_votes) == 1
        assert voter_votes[0].ranked_candidate_ids == ranked_order

    def test_ranked_double_voting_prevented(self, logged_in_voter, ranked_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidates = Candidate.query.filter_by(
            election_id=ranked_election.id).all()

        form_data = {"election_id": ranked_election.id}
        for i, c in enumerate(candidates, start=1):
            form_data[f"ranked_{i}"] = c.id

        # first vote should be valid
        client.post("/voting/submit_vote", data=form_data, follow_redirects=True)

        # second (duplicate) vote should be rejected
        response = client.post("/voting/submit_vote", data=form_data, follow_redirects=True)

        assert b"already voted" in response.data.lower()


class TestBlockchainIntegrity:
    """validates the structure of the blockchain after votes are cast"""

    def test_genesis_block_created_on_startup(self, app_ctx):
        # genesis block (index 0) should have no votes and a previous hash of "0"
        blockchain = app_ctx.blockchain
        assert len(blockchain.chain) >= 1
        genesis = blockchain.chain[0]
        assert genesis.index == 0
        assert genesis.votes == []
        assert genesis.previous_hash == "0"

    def test_chain_is_valid_after_votes(self, logged_in_voter, standard_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        assert app_ctx.blockchain.validate_chain() is True

    def test_chain_links_are_correct(self, logged_in_voter, standard_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        chain = app_ctx.blockchain.chain
        for i in range(1, len(chain)):
            assert chain[i].previous_hash == chain[i - 1].hash, (
                f"Block {i} previous hash does not match hash of block {i - 1}"
            )

    def test_tampered_vote_detected(self, logged_in_voter, standard_election, app_ctx):
        """if votes have been changed then is_valid should return false"""
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        for block in app_ctx.blockchain.chain:
            for vote in block.votes:
                if vote.voter_id == voter_id:
                    vote.candidate_id = 9999  # tamper vote
                    assert vote.is_valid() is False
                    return  # test passed


class TestBlockchainExplorerAPI:
    """
    tests the JSON API endpoints used by the blockchain explorer
    voter anonymity must also be enforced at the API layer
    """

    def test_api_chain_returns_valid_json(self, admin_client, app_ctx):
        # /blockchain/api/chain should return parseable JSON
        response = admin_client.get("/blockchain/api/chain")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "chain" in data
        assert "is_valid" in data

    def test_api_hides_voter_ids(self, logged_in_voter, standard_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        response = client.get("/blockchain/api/chain")
        data = json.loads(response.data)

        for block in data["chain"]:
            for vote in block["votes"]:
                # voter_id should not appear in the API response
                assert "voter_id" not in vote
                assert vote.get("voter_id_hidden") is True

    def test_validate_vote_endpoint_finds_own_vote(self, logged_in_voter, standard_election, app_ctx):
        from models.candidate import Candidate

        voter_id, client = logged_in_voter
        candidate = Candidate.query.filter_by(
            election_id=standard_election.id).first()

        client.post("/voting/submit_vote", data={
            "election_id": standard_election.id,
            "candidate_id": candidate.id
        }, follow_redirects=True)

        response = client.post(
            "/blockchain/api/validate_vote",
            json={
                "voter_id": voter_id,
                "election_id": standard_election.id
            },
            content_type="application/json"
        )
        data = json.loads(response.data)

        assert data["vote_found"] is True
        assert "vote_hash" in data

    def test_validate_vote_cannot_query_other_voter(self, logged_in_voter, standard_election, app_ctx):
        voter_id, client = logged_in_voter

        response = client.post(
            "/blockchain/api/validate_vote",
            json={
                "voter_id": "NOSY-VOTER-SOMEONE",
                "election_id": standard_election.id
            },
            content_type="application/json"
        )
        data = json.loads(response.data)

        assert response.status_code == 403
        assert "unauthorised" in data.get("error", "").lower()

    def test_unauthenticated_user_cannot_access_api(self, client, app_ctx):
        """the bc api needs an active login session"""
        response = client.get(
            "/blockchain/api/chain",
            follow_redirects=False
        )
        assert response.status_code in (302, 401)