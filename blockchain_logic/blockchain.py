from .hash_table import HashTable
from threading import Lock
from blockchain_logic.block import Block
import os
import json
from blockchain_logic.vote import Vote

class Blockchain:
    def __init__(self, blockchain_file="blockchain.json"):
        self.blockchain_file = blockchain_file
        self.chain = []
        self.pending_votes = [] # Votes that are pending to be added to the blockchain
        self.mining_difficulty = 2
        self.block_size = 1 # a new block is created/mined for every vote
        self.vote_registry = HashTable() # Hash table to store votes
        self.chain_lock = Lock()  # ensures only one thread can modify the chain at a time so prevents duplicate votes
        self.create_genesis_block()

        self.load_blockchain() # loads existing bc file

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
            print(f"DEBUG: Adding vote voter_id: {vote.voter_id}, election_id: {vote.election_id}, candidate_id: {vote.candidate_id}")

            if not vote.is_valid():
                # is_valid is a method from the Vote class which checks hash of block
                raise ValueError("Invalid vote")

            if self.__multiple_votes(vote):
                raise ValueError("Voter has already voted")

            self.pending_votes.append(vote)

            self.vote_registry[f"{vote.voter_id}_{vote.election_id}"] = vote  # stores the vote in the hash table
            print(f"DEBUG: Vote added to hash table")

            if len(self.pending_votes) >= self.block_size:
                print("DEBUG: Max block size reached, creating new block")
                self.__add_pending_votes()
            else:
                print(f"DEBUG: Block size not reached ({len(self.pending_votes)}/{self.block_size})")

    def __multiple_votes(self, vote):
        # checks if a voter has already voted via the hash table
        # hash table only stores if a voter has voted in an election, NOT the actual details
        return f"{vote.voter_id}_{vote.election_id}" in self.vote_registry

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

        self.save_blockchain()  # save the blockchain to file after adding a new block

    def add_remaining_votes(self):
        # called when current pending votes need to be added to the blockchain regardless of the block size
        # this is needed when election is ending so remaining votes need to be mined
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

        # we also need to count the votes that are pending in the current block
        for vote in self.pending_votes:
            election_id = vote.election_id
            candidate_id = vote.candidate_id

            if election_id not in results:
                results[election_id] = {}

            results[election_id][candidate_id] = results[election_id].get(candidate_id, 0) + 1

        return results

    def get_blockchain(self):
        # returns entire blockchain as a list of dictionaries
        return [block.to_dict() for block in self.chain]

    def save_blockchain(self):
        # this saves the blockchain to a file in JSON format
        try:
            blockchain_data = {
                "chain": [block.to_dict() for block in self.chain],
                "pending_votes": [vote.to_dict() for vote in self.pending_votes]
            }
            with open(self.blockchain_file, 'w') as file:
                json.dump(blockchain_data, file, indent=2)
            print(f"DEBUG: Blockchain saved to {self.blockchain_file}")
        except Exception as e:
            print(f"DEBUG: Error in saving blockchain: {str(e)}")

    def load_blockchain(self):
        # loads the blockchain from a json file
        # used to maintain persistance when program ends and runs
        try:
            if os.path.exists(self.blockchain_file):
                print(f"DEBUG: Loading blockchain from {self.blockchain_file}")

                with open(self.blockchain_file, 'r') as file:
                    blockchain_data = json.load(file)

                # reconstructing the chain
                self.chain = []
                self.pending_votes = []

                for block_data in blockchain_data.get("chain", []):
                    votes = []
                    for vote_data in block_data.get("votes", []):
                        vote = Vote(
                            voter_id=vote_data["voter_id"],
                            election_id=vote_data["election_id"],
                            candidate_id=vote_data["candidate_id"],
                        )
                        vote.timestamp = vote_data["timestamp"]
                        vote.vote_hash = vote_data["vote_hash"]
                        votes.append(vote)
                        self.vote_registry[f"{vote.voter_id}_{vote.election_id}"] = vote

                    block = Block(
                        index=block_data["index"],
                        votes=votes,
                        previous_hash=block_data["previous_hash"]
                    )
                    block.timestamp = block_data["timestamp"]
                    block.nonce = block_data["nonce"]
                    block.hash = block_data["hash"]
                    self.chain.append(block)

                for vote_data in blockchain_data.get("pending_votes", []):
                    vote = Vote(
                        voter_id=vote_data["voter_id"],
                        election_id=vote_data["election_id"],
                        candidate_id=vote_data["candidate_id"],
                    )
                    vote.timestamp = vote_data["timestamp"]
                    vote.vote_hash = vote_data["vote_hash"]
                    self.pending_votes.append(vote)
                    self.vote_registry[f"{vote.voter_id}_{vote.election_id}"] = vote
                print(f"DEBUG: Loaded {len(self.chain)} blocks and {len(self.pending_votes)} pending votes not yet mined/added.")

                #validate the loaded blockchain
                if not self.validate_chain():
                    print("DEBUG: Loaded blockchain is invalid so creating new genesis block")
                    self.chain = []
                    self.pending_votes = []
                    self.vote_registry = HashTable()
                    self.create_genesis_block()
                    self.save_blockchain()

            else:
                print(f"DEBUG: No blockchain file found so creating new genesis block")
                self.create_genesis_block()
                self.save_blockchain()

        except Exception as e:
            print(f"ERROR: Failed to load blockchain: {str(e)}")
            print("DEBUG: Creating new genesis block")
            self.chain = []
            self.pending_votes = []
            self.vote_registry = HashTable()
            self.create_genesis_block()
            self.save_blockchain()
