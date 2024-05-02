import json

# Transaction request

class Transaction:
    def __init__(self, sender, message, nonce, signature):
        self.sender = sender
        self.message = message
        self.nonce = nonce
        self.signature = signature

    def is_valid(self):
        # sender is an hexadecimal string of 64 alphanumeric characters
        # message is a string that contains at most 70 alphanumeric characters
        # nonce is an integer; starts with 0 and increments before issuing new transaction
        # signature is an hexadecimal string of 128 alphanumeric characters
        pass  # Check validity of properties (message, nonce, etc)

    def format_json(self):
        return {
            "type": "transaction",
            "payload": {
                "sender": self.sender,
                "message": self.message,
                "nonce": self.nonce,
                "signature": self.signature
            }
        }

    def __str__(self):
        return json.dumps(self.format_json())