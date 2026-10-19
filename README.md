# Blockchain Voting Rishi Gupta

This project is a web-based voting platform built with Python and Flask, where every vote is recorded on a custom-built blockchain. The blockchain is built from scratch as an independent project for my learning of blockchain concepts such as hashing, chaining, mining, proof of work, and its applications in the real world. Having worked on this project for over 6 months, there is still a lot more to add to it as it does come with some limitations which I will discuss later on this README.

## Overview of Features

- Custom blockchain without external libraries for the actual blockchain.
- Two voting types (for now): standard and ranked.
- Tamper-evident votes where each vote has its own SHA-256 hash and each block hash covers all of its votes.
- Double-vote prevention using a hash table to give O(1) lookups.
- Controlled registration: admins generate unique voter IDs which can be distributed to the intended users.
- Two-factor authentication: email verification with OTPs generated with Python's secrets module.
- Blockchain explorer which allows users to verify their vote against the chain. Note that other VoterIDs are not visible on the chain.
- Separate admin tools and past elections page.


## The process

Each block stores an index, a list of votes, the hash of the previous block, a timestamp and a nonce (number used once). The block's hash is the SHA-256 of all of that data. Because every block includes its predecessor's hash, changing anything in an old block changes its hash, which no longer matches the previous_hash stored in the next block, so the break is detectable.

Proof of work: Mining means searching for a nonce such that the block's hash starts with a required number of zeros. I have set mine as mining_difficulty = 2 for low computational effort but this is likely to be a larger number when deployed. The only way to find a valid hash is to keep incrementing the nonce and re-hashing. In a real network this cost is what makes rewriting history expensive.

When a vote is cast, the relational database records that a voter has voted but not which voter. The blockchain holds the votes itself and on startup, sync_blockchain_with_database reconciles the two and takes action about any inconsistencies.

I have also utilised different OOP concepts to build the core of this system but I will not go into the details here.

Stack: Python 3.13, Flask, Flask-SQLAlchemy (SQLite by default), Flask-Login, Flask-Mail, Jinja2, HTML/CSS.

## Limitations

This project demonstrates blockchain concepts but does not provide all the guarantees that make real blockchains or elections yet.

Currently this system is not decentralised. A blockchain's security comes from many independent parties each holding a copy of the ledger and agreeing on its state through a consensus protocol. This project has one server and one copy/ledger of the chain (blockchain.json).

The system also currently relies on voter IDs being kept anonymous as they are actually visible on the ledger/chain although not on the explorer. In the future, this will be changed such that votes cannot be linked back to a voter.
