from blockchain_logic.ranked_vote import RankedVote
from blockchain_logic.standard_vote import StandardVote

class VoteBuilder:
    """
    This class creates vote objects
    Provides static methods to create different types of votes
    """

    VOTE_TYPES = {
        "standard": StandardVote,
        "ranked": RankedVote
    }

    @staticmethod
    def create_vote(vote_type, voter_id, election_id, vote_data):
        """
        Creates a vote object based on the vote type

        :param vote_type: string e.g. "standard", "ranked")
        :param voter_id: ID of the voter
        :param election_id: ID of the election
        :param vote_data: Data specific to the vote type
        :return: abstract instance of the appropriate Vote subclass
        """

        # validates the vote type
        if vote_type not in VoteBuilder.VOTE_TYPES:
            raise ValueError(f"Unsupported vote type: {vote_type}")

        # gets vote type class from the dictionary
        vote_class = VoteBuilder.VOTE_TYPES[vote_type]

        if vote_type == "standard":
            # StandardVote expects: voter_id, election_id, candidate_id
            return vote_class(voter_id, election_id, vote_data)
        elif vote_type == "ranked":
            # RankedVote expects: voter_id, election_id, ranked_candidate_ids (list)
            return vote_class(voter_id, election_id, vote_data)

    @staticmethod
    def from_dict(data):
        """
        Reconstructs vote from dictionary for blockchain loading
        :param data: dictionary containing vote_data with vote_type key
        :return: AbstractVote subclass instance
        """

        vote_type = data.get("vote_type")

        if vote_type not in VoteBuilder.VOTE_TYPES:
            raise ValueError(f"Unsupported vote type: {vote_type}")

        vote_class = VoteBuilder.VOTE_TYPES[vote_type]

        # each vote has its own from_dict method so it is called to reconstruct the vote
        return vote_class.from_dict(data)

    @staticmethod
    def get_supported_vote_types():
        """
        Returns a list of supported vote types
        :return: list of strings
        """
        return list(VoteBuilder.VOTE_TYPES.keys())





