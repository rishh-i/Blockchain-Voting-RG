import time
import hashlib

class Vote:
    # class represents a single vote in the blockchain

    def __init__(self, voter_id, election_id, candidate_id):
        self.voter_id = voter_id
        self.election_id = election_id
        self.candidate_id = candidate_id
        self.timestamp = time.time()
        self.vote_hash = self.__calculate_vote_hash()

    def __calculate_vote_hash(self):

        vote_string = f"{self.voter_id}{self.candidate_id}{self.timestamp}"
        return hashlib.sha256(vote_string.encode()).hexdigest()

    def to_dict(self):
        # Converts the block to a dictionary format for JSON serialisation

        return {
            "voter_id": self.voter_id,
            "candidate_id": self.candidate_id,
            "election_id": self.election_id,
            "timestamp": self.timestamp,
            "vote_hash": self.vote_hash
        }

    def is_valid(self):
        return self.vote_hash == self.__calculate_vote_hash()