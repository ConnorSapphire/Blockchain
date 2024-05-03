from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import json
import re

sender_chars = re.compile('^[a-fA-F0-9]{64}$')
signature_chars = re.compile('^[a-fA-F0-9]{128}$')

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
        sender, message, nonce, signature = self.sender, self.message, self.nonce, self.signature

        if not (sender and isinstance(sender, str) and sender_chars.search(sender)):
            return False

        if not (message and isinstance(message, str) and len(message) <= 70 and message.isalnum()):
            return False

        if not (isinstance(nonce, int) and nonce >= 0):
            return False

        if not (signature and isinstance(signature, str) and signature_chars.search(signature)):
            return False

        try:
            public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(sender))
            public_key.verify(bytes.fromhex(self.signature), self.message.encode())
        except Exception:
            return False

        return True

    def format_json(self):
        return {
            "sender": self.sender,
            "message": self.message,
            "nonce": self.nonce,
            "signature": self.signature
        }

    def __str__(self):
        return json.dumps(self.format_json())
