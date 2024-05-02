import json
import hashlib

# Block request

class Block:
    def __init__(self, index, transactions=[], previous_hash=None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.current_hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = {
            "index": self.index,
            "transactions": [t.format_json for t in self.transactions],
            "previous_hash": self.previous_hash
        }
        block_str = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()

    def is_valid(self):
        pass  # Check validity

    def format_json(self):
        return {
            "index": self.index,
            "transactions": [t.format_json for t in self.transactions],
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash
        }

    def __str__(self):
        return json.dumps(self.format_json())
