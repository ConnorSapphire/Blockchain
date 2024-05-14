"""Some of this module was created using altered tutorial code."""

from cryptography.exceptions import InvalidSignature
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
from enum import Enum
import hashlib
import json
import re

sender_valid = re.compile('^[a-fA-F0-9]{64}$')
signature_valid = re.compile('^[a-fA-F0-9]{128}$')

MessageValidationError = Enum('MessageValidationError', ['INVALID_JSON', 'INVALID_SENDER', 'INVALID_MESSAGE', 'INVALID_NONCE', 'INVALID_SIGNATURE'])

def make_transaction(sender, message, nonce, signature) -> str:
    return json.dumps({'type':'transaction',
                    'payload': {'sender': sender, 'message': message, 'nonce': nonce, 'signature': signature}})

def transaction_bytes(transaction: dict) -> bytes:
    return json.dumps({k: transaction.get(k) for k in ['sender', 'message']}, sort_keys=True).encode()

def make_signature(private_key: ed25519.Ed25519PrivateKey, message: str) -> str:
    transaction = {'sender': private_key.public_key().public_bytes_raw().hex(), 'message': message}
    return private_key.sign(transaction_bytes(transaction)).hex()

def validate_message(response: str, node_ip) -> dict | MessageValidationError:
    try:
        res = json.loads(response)
    except json.JSONDecodeError:
        #print(1)
        return MessageValidationError.INVALID_JSON, "error"

    if res['type'] == "values":
        #print(2)
        return validate_request(res), res['type']
    elif res['type'] == "transaction":
        print(f"[NET] Received a transaction from node {node_ip}: {res['payload']}\n")
        #print(3)
        return validate_transaction(res), res['type']
    else:
        #print(4)
        return MessageValidationError.INVALID_JSON, "error"


def validate_transaction(transaction: dict) -> dict | MessageValidationError:
    if not(transaction.get('payload') and isinstance(transaction['payload'], dict)):
        return MessageValidationError.INVALID_JSON
    
    tx = transaction['payload']
 
    if not(tx.get('sender') and isinstance(tx['sender'], str) and sender_valid.search(tx['sender'])):
        print(f"[TX] Received an invalid transaction, wrong sender - {tx}\n")
        return MessageValidationError.INVALID_SENDER

    if not(tx.get('message') and isinstance(tx['message'], str) and len(tx['message']) <= 70 and tx['message'].isalnum()):
        print(f"[TX] Received an invalid transaction, wrong message - {tx}\n")
        return MessageValidationError.INVALID_MESSAGE

    try:
        if not (isinstance(tx['nonce'], int) and tx['nonce'] >= 0):
            print(f"[TX] Received an invalid transaction, wrong nonce - {tx}\n")
            return MessageValidationError.INVALID_NONCE
    except KeyError:
        print(f"[TX] Received an invalid transaction, wrong nonce - {tx}\n")
        return MessageValidationError.INVALID_NONCE

    public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(tx['sender']))
    if not(tx.get('signature') and isinstance(tx['signature'], str) and signature_valid.search(tx['signature'])):
        print(f"[TX] Received an invalid transaction, wrong signature message - {tx}\n")
        return MessageValidationError.INVALID_SIGNATURE
    try:
        public_key.verify(bytes.fromhex(tx['signature']), transaction_bytes(tx))
    except InvalidSignature:
        print(f"[TX] Received an invalid transaction, wrong signature message - {tx}\n")
        return MessageValidationError.INVALID_SIGNATURE

    return transaction

def validate_request(request: dict) -> dict | MessageValidationError:
    try:
        if not(isinstance(request['payload'], int), request['payload'] >= 0):
            return MessageValidationError.INVALID_JSON
    except KeyError:
        return MessageValidationError.INVALID_JSON
    req = request['payload']
    return request
    
    

class Blockchain():
    def  __init__(self):
        self.blockchain = []
        self.pool = []
        self.current_proposals = []
        self.new_block('0' * 64)

    def new_block(self, previous_hash=None, proposal = None) -> None:
        block = proposal or self.new_proposal(previous_hash)
        if len(self.pool) > 0 and block['transactions'][0] == self.pool[0]:
            self.pool.pop(0)
        self.blockchain.append(block)
  
    def new_proposal(self, previous_hash=None) -> dict:
        block = {
            'index': len(self.blockchain),
            'transactions': [] if len(self.pool) == 0 else [self.pool[0]],
            'previous_hash': previous_hash or self.blockchain[-1]['current_hash'],
        }
        block['current_hash'] = self.calculate_hash(block)
        self.current_proposals.append(block)
        return block

    def last_block(self) -> dict:
        return self.blockchain[-1]

    def calculate_hash(self, block: dict) -> str:
        block_object: str = json.dumps({k: block.get(k) for k in ['index', 'transactions', 'previous_hash']}, sort_keys=True)
        block_string = block_object.encode()
        raw_hash = hashlib.sha256(block_string)
        hex_hash = raw_hash.hexdigest()
        return hex_hash

    def add_transaction(self, transaction: dict) -> bool:
        if isinstance(transaction, dict) and transaction not in self.pool:
            self.pool.append(transaction)
            return True
        return False
