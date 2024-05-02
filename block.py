import json

# Block request

class Block:
    def __init__(self, index, previous_hash, transactions=[]):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.current_hash = self.calculate_hash()

    def calculate_hash(self):
        return 1

    def is_valid(self):
        pass  # Check validity

    def format_json(self):
        obj = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash
        }

        t_list = []
        for t in self.transaction:
            t_list.append(t.format_json)
        obj["transactions"] = t_list

        return obj

    def __str__(self):
        return json.dumps(self.format_json())