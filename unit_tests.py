import unittest
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch

def setUpModule():
    patch('builtins.print').start()

def tearDownModule():
    patch.stopall()

from blockchain_logic.hash_table import HashTable

class TestHashTable(unittest.TestCase):

    def setUp(self):
        self.hash_table = HashTable()

    def test_insert_and_get(self):
        """Test if inserted key-value pairs can be retrieved correctly."""
        self.hash_table.insert("voter1_1", "vote_obj")
        self.assertEqual(self.hash_table.get("voter1_1"), "vote_obj")

    def test_get_missing_key_returns_none(self):
        """Test if getting a non-existent key returns none rather than an error"""
        self.assertIsNone(self.hash_table.get("non_existent_key"))

    def test_contains_existing_key(self):
        """Tests if __contains__ returns true for an inserted key"""
        self.hash_table.insert("voter2_1", "vote_obj")
        self.assertIn("voter2_1", self.hash_table)

    def test_contains_missing_key(self):
        """else __contains__ should return false for a non existent key"""
        self.assertNotIn("voter99_99", self.hash_table)

    def test_update_existing_key(self):
        """inserting key should overwrite existing value"""
        self.hash_table.insert("voter3_1", "old_value")
        self.hash_table.insert("voter3_1", "new_value")
        self.assertEqual(self.hash_table.get("voter3_1"), "new_value")

    def test_delete_existing_key(self):
        """Test if deleting an existing key removes it from the hash table."""
        self.hash_table.insert("voter4_1", "vote_obj")
        result = self.hash_table.delete("voter4_1")
        self.assertTrue(result)
        self.assertIsNone(self.hash_table.get("voter4_1"))

    def test_delete_missing_key_returns_false(self):
        """Tests if deleting a missing key returns false rather than an error."""
        self.assertFalse(self.hash_table.delete("imaginary_key"))

    def test_collision_handling(self):
        """Test if multiple entries are stored correctly"""
        ht = HashTable(size=1)  # Force collisions by using a hash table of size 1
        ht.insert("a", 1)
        ht.insert("b", 2)
        ht.insert("c", 3)
        self.assertEqual(ht.get("a"), 1)
        self.assertEqual(ht.get("b"), 2)
        self.assertEqual(ht.get("c"), 3)


from blockchain_logic.standard_vote import StandardVote

class TestStandardVote(unittest.TestCase):

    def setUp(self):
        self.vote = StandardVote(voter_id="voter1", election_id=1, candidate_id=42)

    def test_attributes_set_correctly(self):
        """A SHA-256 hash should be computed when vote is created"""
        self.assertIsNotNone(self.vote.vote_hash)
        self.assertEqual(len(self.vote.vote_hash), 64)

    def test_is_valid_unmodified(self):
        self.assertTrue(self.vote.is_valid())

    def test_tampered_candidate_id_fails_validation(self):
        """Changing the candidate_id after creation should invalidate the hash"""
        self.vote.candidate_id = 67
        self.assertFalse(self.vote.is_valid())

    def test_tampered_voter_id_fails_validation(self):
        self.vote.voter_id = "rghacker"
        self.assertFalse(self.vote.is_valid())

    def test_validate_vote_data_valid(self):
        self.assertTrue(self.vote.validate_vote_data())

    def test_validate_vote_data_zero_candidate(self):
        """candidate id of 0 should be invalid and raise valueerror"""
        self.vote.candidate_id = 0
        with self.assertRaises(ValueError):
            self.vote.validate_vote_data()

    def test_validate_vote_data_negative_candidate(self):
        self.vote.candidate_id = -2210
        with self.assertRaises(ValueError):
            self.vote.validate_vote_data()

from blockchain_logic.ranked_vote import RankedVote

class TestRankedVote(unittest.TestCase):

    def setUp(self):
        self.vote = RankedVote(voter_id="voter2", election_id=2, ranked_candidate_ids=[3,1,2])

    def test_attributes_set_correctly(self):
        self.assertEqual(self.vote.voter_id, "voter2")
        self.assertEqual(self.vote.election_id, 2)
        self.assertEqual(self.vote.ranked_candidate_ids, [3,1,2])

    def test_hash_generated_on_creation(self):
        self.assertIsNotNone(self.vote.vote_hash)
        self.assertEqual(len(self.vote.vote_hash), 64)

    def test_is_valid_unmodified(self):
        self.assertTrue(self.vote.is_valid())

    def test_tampered_rankings_fails_validation(self):
        self.vote.ranked_candidate_ids = [1,2,3]
        self.assertFalse(self.vote.is_valid())

    def test_validate_empty_list_raises(self):
        self.vote.ranked_candidate_ids = []
        with self.assertRaises(ValueError):
            self.vote.validate_vote_data()

    def test_validate_non_list_raises(self):
        self.vote.ranked_candidate_ids = "uh oh no votes"
        with self.assertRaises(ValueError):
            self.vote.validate_vote_data()

    def test_validate_duplicate_candidates_raises(self):
        self.vote.ranked_candidate_ids = [1,1,2]
        with self.assertRaises(ValueError):
            self.vote.validate_vote_data()

    def test_validate_invalid_candidate_id_types_raises(self):
        self.vote.ranked_candidate_ids = ["r", "g"]
        with self.assertRaises(ValueError):
            self.vote.validate_vote_data()

from blockchain_logic.vote_builder import VoteBuilder

class TestVoteBuilder(unittest.TestCase):

    def test_create_standard_vote(self):
        vote = VoteBuilder.create_vote("standard", "v1", 1, 5)
        self.assertIsInstance(vote, StandardVote)
        self.assertEqual(vote.candidate_id, 5)

    def test_create_ranked_vote(self):
        vote = VoteBuilder.create_vote("ranked", "v2", 2, [3,1,2])
        self.assertIsInstance(vote, RankedVote)
        self.assertEqual(vote.ranked_candidate_ids, [3,1,2])

    def test_create_invalid_vote_type(self):
        with self.assertRaises(ValueError):
            VoteBuilder.create_vote("nondemocratic", "v3", 3, 1)

    def test_from_dict_standard(self):
        original = VoteBuilder.create_vote("standard", "v4", 1, 7)
        restored = VoteBuilder.from_dict(original.to_dict())
        self.assertIsInstance(restored, StandardVote)
        self.assertTrue(restored.is_valid())

    def test_from_dict_ranked(self):
        original = VoteBuilder.create_vote("ranked", "v5", 2, [2,1])
        restored = VoteBuilder.from_dict(original.to_dict())
        self.assertIsInstance(restored, RankedVote)
        self.assertTrue(restored.is_valid())

    def test_from_dict_unknown_type(self):
        with self.assertRaises(ValueError):
            VoteBuilder.from_dict({"vote_type": "unknown"})


from blockchain_logic.block import Block

class TestBlock(unittest.TestCase):

    def make_vote(self):
        return StandardVote(voter_id="voter1", election_id=1, candidate_id=5)

    def test_block_created_with_correct_attributes(self):
        vote = self.make_vote()
        block = Block(index=1, votes=[vote], previous_hash="1212aab")
        self.assertEqual(block.index, 1)
        self.assertEqual(block.previous_hash, "1212aab")
        self.assertEqual(len(block.votes), 1)

    def test_hash_is_generated_on_creation(self):
        block = Block(index=0, votes=[], previous_hash="0")
        self.assertIsNotNone(block.hash)
        self.assertEqual(len(block.hash), 64)

    def test_mine_block_valid_hash(self):
        """when a block is mined its hash should begin with a required number of zeros"""
        block = Block(index=1, votes=[], previous_hash="0")
        block.mine_block(difficulty=2)
        self.assertTrue(block.hash.startswith("00"))

    def test_is_valid_after_mining(self):
        block = Block(index=1, votes=[], previous_hash="0")
        block.mine_block(difficulty=2)
        self.assertTrue(block.is_valid())

    def test_tampered_block_is_invalid(self):
        block = Block(index=1, votes=[], previous_hash="0")
        block.mine_block(difficulty=2)
        block.previous_hash = "let me change this no one will know"
        self.assertFalse(block.is_valid())


from blockchain_logic.blockchain import Blockchain

class TestBlockchain(unittest.TestCase):

    def setUp(self):
        # use a temp file for the bc
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.bc = Blockchain(self.tmp.name)

    def remove_tmp_file(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def make_vote(self, voter_id="v1", election_id=1, candidate_id=10):
        return VoteBuilder.create_vote("standard", voter_id, election_id, candidate_id)

    def test_genesis_block_created_on_init(self):
        self.assertEqual(len(self.bc.chain), 1)

    def test_genesis_block_has_no_votes(self):
        self.assertEqual(len(self.bc.chain[0].votes), 0)

    def test_add_vote_creates_new_block(self):
        """block size = 1 so every vote should create a new block"""
        self.bc.add_vote(self.make_vote())
        self.assertEqual(len(self.bc.chain), 2)

    def test_double_vote_raises(self):
        """adding the same voter election pair twice raises error"""
        self.bc.add_vote(self.make_vote())
        with self.assertRaises(ValueError):
            self.bc.add_vote(self.make_vote())

    def test_different_elections_same_voter(self):
        self.bc.add_vote(self.make_vote(voter_id="v1", election_id=1))
        self.bc.add_vote(self.make_vote(voter_id="v1", election_id=2))
        self.assertEqual(len(self.bc.chain), 3)

    def test_different_voters_same_election(self):
        self.bc.add_vote(self.make_vote(voter_id="v1", election_id=1))
        self.bc.add_vote(self.make_vote(voter_id="v2", election_id=1))
        self.assertEqual(len(self.bc.chain), 3)

    def test_valid_chain(self):
        self.bc.add_vote(self.make_vote())
        self.assertTrue(self.bc.validate_chain())

    def test_chain_detects_tampering(self):
        self.bc.add_vote(self.make_vote())
        self.bc.chain[1].previous_hash = "wow so easy to change"
        self.assertFalse(self.bc.validate_chain())


if __name__ == "__main__":
    unittest.main(verbosity=2)
