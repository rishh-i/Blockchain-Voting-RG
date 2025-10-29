import time
import hashlib
import json

class Block:
    # represents a single block in the blockchain

    def __init__(self, index, votes, previous_hash):
        self.index = index
        self.votes = votes
        self.previous_hash = previous_hash
        self.timestamp = time.time()
        self.nonce = 0 # short for "number used once", represents how many attempts were made to find a valid hash
        self.hash = self.__calculate_hash()

    def __calculate_hash(self):
        #private method to calculate the hash of the block

        votes_string = json.dumps([vote.to_dict() for vote in self.votes], sort_keys=True)
        block_string = f"{self.index}{votes_string}{self.previous_hash}{self.timestamp}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty=2):
        # difficulty of 2 corresponds to the number of leading zeros required in the hash i.e. larger difficulty requires more computational work
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