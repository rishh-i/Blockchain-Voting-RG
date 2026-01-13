import time
import hashlib

class AbstractVote:
    """
    This is an abstract base class used for all vote types
    """

    def __init__(self, voter_id, election_id):
        self.voter_id = voter_id
        self.election_id = election_id
        self.timestamp = time.time()
        self.vote_hash = None

    def _calculate_vote_hash(self):
        """
        abstract method
        every vote type must implement its own hash calculation
        """
        raise NotImplementedError("Subclasses must implement this method")

    def to_dict(self):
        # abstract method
        raise NotImplementedError("Subclasses must implement this method")

    def get_vote_data(self):
        # abstract method
        raise NotImplementedError("Subclasses must implement this method")

    def validate_vote_data(self):
        # abstract method
        raise NotImplementedError("Subclasses must implement this method")

    def is_valid(self):
        # this method is NOT abstract so will be inherited by all subclasses
        return self.vote_hash == self._calculate_vote_hash()

    def get_vote_type(self):
        # method inherited by all subclasses
        return self.__class__.__name__