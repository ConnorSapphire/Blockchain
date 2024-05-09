import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
import socket

from blockchain import make_signature, make_transaction
from network import recv_prefixed, send_prefixed

# TODO generate a private key and create a transaction using make_signature and make_transaction
# using the derived public key as the sender
private_key = ed25519.Ed25519PrivateKey.generate()
sender = private_key.public_key().public_bytes_raw().hex()
message = "BOO"
nonce = 0
signature = make_signature(private_key, message)
transaction = make_transaction(sender, message, nonce, signature)

# TODO create a socket and connect to the blockchain node
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.137.1', 6002))

# TODO send the transaction, receive the response and print it
print(f"SENDING:\n{transaction}")
send_prefixed(s, transaction.encode())
try:
    data = recv_prefixed(s).decode()
    print(f"RESPONSE:\n{data}")
except Exception as e:
    print(e)
