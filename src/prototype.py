import hashlib
import time
import json
import os

# Prototype of a simple blockchain implementation in Python
# self.data example: {"voter_id": voter_id_hash, "vote": candidate_name}
# self.proof_number is an integer that starts at 0 and is incremented until the block's hash meets the required difficulty

class Block:
    # Represents a single block in the blockchain

    def __init__(self, index, votes, previous_hash, timestamp = None):
        self.index = index
        self.votes = votes
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.nonce = 0 # for proof of work
        self.hash = self.calculate_hash()

    def _calculate_hash(self): #private method to calculate the hash of the block

        votes_string = json.dumps([vote.to_dict() for vote in self.votes], sort_keys=True)
        block_string = f"{self.index}{votes_string}{self.previous_hash}{self.timestamp}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty=2):

        while self.hash[:difficulty] != '0' * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

    def to_dict(self):
        # Converts the block to a dictionary format for JSON serialization

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
        return self.hash == self.calculate_hash()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_votes = [] # Votes that are pending to be added to the blockchain
        self.mining_difficulty = 2
        self.mining_reward = 10
        self.block_size = 5
        #self.vote_registry = HashTable()  # Placeholder for a more complex structure if needed
        #self.chain_lock = Lock()  # Placeholder for thread safety if needed

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
