from blockchain_logic.hash_table import HashTable
from threading import Lock
from blockchain_logic.block import Block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_votes = [] # Votes that are pending to be added to the blockchain
        self.mining_difficulty = 2
        self.block_size = 5
        self.vote_registry = HashTable() # Hash table to store votes
        self.chain_lock = Lock()  # ensures only one thread can modify the chain at a time so prevents duplicate votes
        self.create_genesis_block()

    def create_genesis_block(self):
        # genesis block has no previous hash and has no votes

        genesis_block = Block(0, [], "0")
        genesis_block.mine_block(self.mining_difficulty)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1]

    def add_vote(self, vote):
        # adds and validates a vote before adding it to the pending votes

        with self.chain_lock:

            if not vote.is_valid():
                raise ValueError("Invalid vote")

            if self.__multiple_votes(vote):
                raise ValueError("Voter has already voted")

            self.pending_votes.append(vote)

            self.vote_registry[f"{vote.voter_id}_{vote.election_id}"] = vote  # stores the vote in the hash table
            ##self.vote_registry.insert(f"{vote.voter_id}_{vote.election_id}", vote) # stores the vote in the hash table

            if len(self.pending_votes) >= self.block_size:
                self.__add_pending_votes()

    def __multiple_votes(self, vote):
        # checks if a voter has already voted through the hash table

        return f"{vote.voter_id}_{vote.election_id}" in self.vote_registry
        ## return self.vote_registry.get(f"{vote.voter_id}_{vote.election_id}") is not None

    def __add_pending_votes(self):
        # creates a new block with the pending votes and adds it to the blockchain

        if not self.pending_votes:
            return # if there are no pending votes, do nothing, although this is validated in the add_vote method

        new_index = len(self.chain)
        previous_hash = self.get_latest_block().hash
        new_block = Block(new_index, self.pending_votes.copy(), previous_hash)
        new_block.mine_block(self.mining_difficulty)
        self.chain.append(new_block)
        self.pending_votes = []  # clear pending votes after adding to the blockchain

    def __add_remaining_votes(self):
        # called when current pending votes need to be added to the blockchain regardless of the block size

        with self.chain_lock:
            if self.pending_votes:
                self.__add_pending_votes()

    def validate_chain(self):

        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if not current_block.is_valid():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

            for vote in current_block.votes: # validates all votes in block
                if not vote.is_valid():
                    return False
        return True

    def get_results(self):
        results = {}
        for block in self.chain:
            for vote in block.votes:
                election_id = vote.election_id
                candidate_id = vote.candidate_id

                if election_id not in results:
                    results[election_id] = {}

                results[election_id][candidate_id] = results[election_id].get(candidate_id, 0) + 1 # increments the vote count for the candidate, or starts at 0 if candidate_id not found
        return results

    def get_blockchain(self):
        # returns entire blockchain as a list of dictionaries
        return [block.to_dict() for block in self.chain]