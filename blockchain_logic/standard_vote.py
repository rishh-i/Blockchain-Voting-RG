import hashlib
from blockchain_logic.abstract_vote import AbstractVote

class StandardVote(AbstractVote):
    """
    Standard votes: user selects one candidate to vote for
    Inherits from AbstractVote and overrides necessary methods
    """

    def __init__(self, voter_id, election_id, candidate_id):
        super().__init__(voter_id, election_id)
        self.candidate_id = candidate_id
        self.vote_hash = self._calculate_vote_hash()

    def _calculate_vote_hash(self):
        # calculates hash which includes candidate_id, voter_id, and timestamp
        vote_string = f"{self.voter_id}{self.candidate_id}{self.timestamp}"
        return hashlib.sha256(vote_string.encode()).hexdigest()

    def to_dict(self):
        # converts the vote to a dictionary format for JSON format
        return {
            "vote_type": "standard",
            "voter_id": self.voter_id,
            "candidate_id": self.candidate_id,
            "election_id": self.election_id,
            "timestamp": self.timestamp,
            "vote_hash": self.vote_hash
        }

    def get_vote_data(self):
        return self.candidate_id

    def validate_vote_data(self):
        # checks if candidate id is valid
        if not isinstance(self.candidate_id, int) or self.candidate_id <= 0:
            raise ValueError("Invalid candidate ID")
        return True

    @staticmethod
    def from_dict(data):
        """
        Method to create a StandardVote object from a dictionary
        It is used when loading votes from blockchain
        """

        vote = StandardVote(
            voter_id=data["voter_id"],
            election_id=data["election_id"],
            candidate_id=data["candidate_id"]
        )
        vote.timestamp = data["timestamp"]
        vote.vote_hash = data["vote_hash"]
        return vote