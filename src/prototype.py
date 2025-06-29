import hashlib
import time
import json
import os

# Prototype of a simple blockchain implementation in Python
# self.data example: {"voter_id": voter_id_hash, "vote": candidate_name}
# self.proof_number is an integer that starts at 0 and is incremented until the block's hash meets the required difficulty
class Block:
    def __init__(self, index, previous_hash, timestamp, data, proof_number=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.proof_number = proof_number
        self.hash = self.calculate_hash()

    # converts all block data to a string and hashes it using SHA-256
    def calculate_hash(self):
        block_string = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.proof_number}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        while self.hash[:difficulty] != '0' * difficulty:
            self.proof_number += 1
            self.hash = self.calculate_hash()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2

    def create_genesis_block(self):
        return Block(0, '0' * 32, time.time(), 'genesis_block')

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def count_votes(self):
        vote_counts = {}
        for block in self.chain[1:]:
            candidate = block.data.get("vote")
            if candidate:
                vote_counts[candidate] = vote_counts.get(candidate, 0) + 1
        return vote_counts

    def find_vote(self, voter_id_hash):
        for block in self.chain[1:]:
            if block.data.get("voter_id") == voter_id_hash:
                return block.data
        return None
