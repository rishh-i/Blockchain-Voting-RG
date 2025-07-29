import hashlib
import time
import json
from threading import Lock
from hash_table import HashTable

class Vote:
    # class represents a single vote in the blockchain

    def __init__(self, voter_id, candidate_id, timestamp=None):
        self.voter_id = voter_id
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
            "timestamp": self.timestamp,
            "vote_hash": self.vote_hash
        }

    def is_valid(self):
        return self.vote_hash == self.__calculate_vote_hash()


class Block:
    # Represents a single block in the blockchain

    def __init__(self, index, votes, previous_hash, timestamp = None):
        self.index = index
        self.votes = votes
        self.previous_hash = previous_hash
        self.timestamp = time.time()
        self.nonce = 0 # for proof of work
        self.hash = self.__calculate_hash()

    def __calculate_hash(self):
        #private method to calculate the hash of the block

        votes_string = json.dumps([vote.to_dict() for vote in self.votes], sort_keys=True)
        block_string = f"{self.index}{votes_string}{self.previous_hash}{self.timestamp}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty=2):

        while self.hash[:difficulty] != '0' * difficulty:
            self.nonce += 1
            self.hash = self.__calculate_hash()
        print(f"Block mined: {self.hash}")

    def to_dict(self):
        # Converts the block to a dictionary format for JSON serialisation

        return {
            "index": self.index,
            "votes": [vote.to_dict() for vote in self.votes],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }

    def is_valid(self):
        # Checks if stored hash matches the calculated hash
        return self.hash == self.__calculate_hash()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_votes = [] # Votes that are pending to be added to the blockchain
        self.mining_difficulty = 2
        self.mining_reward = 10
        self.block_size = 5
        self.vote_registry = HashTable() # Hash table to store votes
        self.chain_lock = Lock()  # ensures only one thread can modify the chain at a time so prevents duplicate votes

        self.create_genesis_block()

    def create_genesis_block(self):
        # genesis block has no previous hash and has no votes

        genesis_block = Block(0, [], "0", time.time())
        genesis_block.mine_block(self.mining_difficulty)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1]

    def add_vote(self, vote):
        # adds and validates a vote before adding it to the pending votes

        with self.chain_lock:

            if not vote.is_valid():
                raise ValueError("Invalid vote")

            if self.__multiple_votes(vote.voter_id):
                raise ValueError("Voter has already voted")

            self.pending_votes.append(vote)

            self.vote_registry.insert(f"{vote.voter_id}", vote) # stores the vote in the hash table

            if len(self.pending_votes) >= self.block_size:
                self.__add_pending_votes()


    def __multiple_votes(self, voter_id):
        # checks if a voter has already voted through the hash table
        return self.vote_registry.get(f"{voter_id}") is not None

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
                candidate_id = vote.candidate_id
                results[candidate_id] = results.get(candidate_id, 0) + 1 # increments the vote count for the candidate, or starts at 0 if candidate_id not found
        return results

    def get_blockchain(self):
        # returns entire blockchain as a list of dictionaries
        return [block.to_dict() for block in self.chain]