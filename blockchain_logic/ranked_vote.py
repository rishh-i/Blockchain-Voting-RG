import hashlib
import json
from blockchain_logic.abstract_vote import AbstractVote

class RankedVote(AbstractVote):
    """
    Ranked choice votes: user ranks options based on preference
    inherits from AbstractVote and overrides necessary methods
    """

    def __init__(self, voter_id, election_id, ranked_candidate_ids):
        """
        Arguments:
        voter_id - ID of the voter
        election_id - ID of the election
        ranked_candidate_ids - list of candidate IDs in ranked order
        """

        super().__init__(voter_id, election_id)
        self.ranked_candidate_ids = ranked_candidate_ids
        self.vote_hash = self._calculate_vote_hash()

    def _calculate_vote_hash(self):
        # separate method required to calculate ranked selection hash
        ranked_string = json.dumps(self.ranked_candidate_ids, sort_keys=False)
        vote_string = f"{self.voter_id}{ranked_string}{self.timestamp}"
        return hashlib.sha256(vote_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "vote_type": "ranked",
            "voter_id": self.voter_id,
            "ranked_candidate_ids": self.ranked_candidate_ids,
            "election_id": self.election_id,
            "timestamp": self.timestamp,
            "vote_hash": self.vote_hash
        }

    def get_vote_data(self):
        return self.ranked_candidate_ids

    def validate_vote_data(self):
        # checks if ranked candidate ids is a valid list of integers

        # checks data type
        if not isinstance(self.ranked_candidate_ids, list):
            raise ValueError("ranked_candidate_ids must be a list")

        # null validation
        if len(self.ranked_candidate_ids) == 0:
            raise ValueError("ranked_candidate_ids cannot be empty")

        # validate each candidate ID
        for cid in self.ranked_candidate_ids:
            if not isinstance(cid, int) or cid <= 0:
                raise ValueError("Invalid candidate ID in ranked_candidate_ids")

        # validate against duplicates using set
        if len(self.ranked_candidate_ids) != len(set(self.ranked_candidate_ids)):
            raise ValueError("Duplicate candidate IDs found in ranked_candidate_ids")

        return True

    def get_first_choice(self):
        # helper method unique to RankedVote
        if self.ranked_candidate_ids:
            return self.ranked_candidate_ids[0]
        return None

    def get_choice_at_rank(self, rank):
        # helper method unique to RankedVote
        if 0 <= rank < len(self.ranked_candidate_ids):
            return self.ranked_candidate_ids[rank]
        return None

    @staticmethod
    def from_dict(data):
        # used when loading data from blockchain

        vote = RankedVote(
            voter_id=data["voter_id"],
            election_id=data["election_id"],
            ranked_candidate_ids=data["ranked_candidate_ids"]
        )
        vote.timestamp = data["timestamp"]
        vote.vote_hash = data["vote_hash"]
        return vote