from collections import defaultdict # automatically creates a default value for missing keys


class AbstractResultsCalculator:
    """
    Abstract class for calculating election results
    """

    def __init__(self, election_id, votes, candidates):
        """
        Initialises the results calculator

        :param election_id: ID of the election
        :param votes: list of vote objects from blockchain
        :param candidates: list of candidate objects
        """
        self.election_id = election_id
        self.votes = votes
        self.candidates = candidates

    def calculate_results(self):

        election_votes = self._filter_votes()

        valid_votes = self._validate_votes(election_votes)

        vote_counts = self._count_votes(valid_votes)

        winner_data = self._determine_winners(vote_counts)

        return self._format_results(vote_counts, winner_data)

    def _filter_votes(self):
        # inherited by all subclasses

        return [vote for vote in self.votes if vote.election_id == self.election_id]

    def _validate_votes(self, votes):
        # abstract method to be implemented by subclasses
        raise NotImplementedError("implement _validate_votes() method")

    def _count_votes(self, votes):
        # abstract method to be implemented by subclasses
        raise NotImplementedError("implement _count_votes() method")

    def _determine_winners(self, vote_counts):
        # abstract method to be implemented by subclasses
        raise NotImplementedError("implement _determine_winners() method")

    def _format_results(self, vote_counts, winner_data):
        # inherited by all subclasses

        results = {
            "election_id": self.election_id,
            "vote_counts": vote_counts,
            "winner_data": winner_data,
            "total_votes": len(self.votes)
        }

        return results


class StandardResultsCalculator(AbstractResultsCalculator):
    """
    Results calculator for standard voting
    inherits from AbstractResultsCalculator and implements its abstract methods
    """

    def _validate_votes(self, votes):
        # implement vote validation logic specific to standard voting

        valid_votes = []
        candidate_ids = {c.id for c in self.candidates} #c for candidate in candidates

        for vote in votes:
            if vote.get_vote_data() in candidate_ids: # uses method from StandardVote to get candidate_id
                valid_votes.append(vote)

        return valid_votes

    def _count_votes(self, votes):
        # implements vote counting logic specific to standard voting

        vote_counts = defaultdict(int)

        for vote in votes:
            candidate_id = vote.get_vote_data()
            vote_counts[candidate_id] += 1

        return dict(vote_counts)

    def _determine_winners(self, vote_counts):
        # implements winner calc logic specific to standard voting (finds candidate with most votes)

        if not vote_counts:
            return {"winner_id": None, "winning_votes": 0}

        winner_id = max(vote_counts, key=vote_counts.get)
        winning_votes = vote_counts[winner_id]

        # checks for candidates with same number of winning votes
        tied_candidates = [] # list comprehension could be used
        for candidate_id, votes in vote_counts.items():
            if votes == winning_votes:
                tied_candidates.append(candidate_id)

        return {
            "winner_id": winner_id,
            "winning_votes": winning_votes,
            "is_tie": len(tied_candidates) > 1,
            "tied_candidates": tied_candidates if len(tied_candidates) > 1 else []
        }


class RankedResultsCalculator(AbstractResultsCalculator):
    """
    Results calculator for ranked voting
    inherits from AbstractResultsCalculator and implements its abstract methods
    """

    def _validate_votes(self, votes):

        valid_votes = []
        candidate_ids = {c.id for c in self.candidates}

        for vote in votes:
            ranked_ids = vote.get_vote_data()  # uses method from RankedVote to get ranked_candidate_ids

            # checks if all ranked candidate ids exist
            if all(cid in candidate_ids for cid in ranked_ids):
                valid_votes.append(vote)

        return valid_votes

    def _count_votes(self, votes):
        """
        implpements instant runoff algorithm:
        1. Count first choice votes
        2. If there is no majority, eliminate the candidate with the fewest votes
        3. Redistribute votes of eliminated candidate to next choice
        4. Repeat until a candidate has majority
        """

        rounds = []
        active_votes = votes.copy()
        eliminated = set()

        while True:
            # count current round
            round_counts = self._count_current_round(active_votes, eliminated)
            total_votes = sum(round_counts.values())

            rounds.append(round_counts.copy())

            # checks for majority
            if round_counts:
                max_votes = max(round_counts.values())
                if max_votes > total_votes / 2:
                    # majority achieved
                    break

                #majority not achieved so eliminate candidate with least votes
                min_votes = min(round_counts.values())

                candidates_to_eliminate = [] # again could also use list comprehension
                for candidate_id, votes in round_counts.items():
                    if votes == min_votes:
                        candidates_to_eliminate.append(candidate_id)

                eliminated.add(candidates_to_eliminate[0])

                # checks if only one candidate remains
                if len(round_counts) - len(eliminated) <= 1:
                    break

            else:
                break

        return {"rounds": rounds, "final_counts": rounds[-1] if rounds else {}}

    def _count_current_round(self, votes, eliminated):

        counts = defaultdict(int) # every missing key will default to 0

        for vote in votes:
            ranked_ids = vote.get_vote_data()

            # find first non-eliminated candidate in ranked list
            for candidate_id in ranked_ids:
                if candidate_id not in eliminated:
                    counts[candidate_id] += 1
                    break

        return dict(counts)

    def _determine_winners(self, vote_counts):

        final_counts = vote_counts.get("final_counts", {})

        if not final_counts:
            return {
                "winner_id": None,
                "winning_votes": 0,
                "rounds": vote_counts.get("rounds", [])
            }

        winner_id = max(final_counts, key=final_counts.get)
        winning_votes = final_counts[winner_id]

        return {
            "winner_id": winner_id,
            "winning_votes": winning_votes,
            "rounds": vote_counts.get("rounds", []),
            "total_rounds": len(vote_counts.get("rounds", []))
        }


class ResultsCalculator:
    """
    Creates appropriate results calculator based on vote type
    """

    @staticmethod
    def create_calculator(vote_type, election_id, votes, candidates):
        """

        :param vote_type: string e.g. "standard", "ranked"
        :param election_id: ID of the election
        :param votes: list of vote objects from blockchain
        :param candidates: list of candidate objects
        :return: instance of appropriate AbstractResultsCalculator subclass
        """

        if vote_type == "standard":
            return StandardResultsCalculator(election_id, votes, candidates)
        elif vote_type == "ranked":
            return RankedResultsCalculator(election_id, votes, candidates)
        else:
            raise ValueError(f"Unsupported vote type: {vote_type}")
