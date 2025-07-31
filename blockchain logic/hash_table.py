class HashTable:

    """
    Key: string (voter_id_election_id)
    Value: Vote object
    """

    def __init__(self, size=100):
        # initialises a hash table with an empty buckets
        # each slot is a list to handle collisions via chaining
        self.size = size
        self.table = [[] for _ in range(self.size)]

    def __hash(self, key):
        return hash(key) % self.size # modulus keeps value within bounds of the table size

    def insert(self, key, value):
        # adds or updates a key-value pair in the hash table which is a vote in this case
        index = self.__hash(key)
        bucket = self.table[index]
        for i, (k, v) in enumerate(bucket): # k represents the key and v represents the value
            if k == key:
                bucket[i] = (key, value)
                return # simply ends the function if key already exists

        bucket.append((key, value))  # if key not found, append new key-value pair

    def get(self, key):
        # gets value for a given key from the hash table else returns none if key not found
        index = self.__hash(key)
        bucket = self.table[index]
        for k, v in bucket: # k represents the key and v represents the value
            if k == key:
                return v
        return None

    def delete(self, key):
        # deletes a key-value pair from the hash table
        # returns true if deleted, false if key not found
        index = self.__hash(key)
        bucket = self.table[index]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                return True
        return False