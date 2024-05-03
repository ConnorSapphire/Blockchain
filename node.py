from block import Block
from transaction import Transaction
from network import *

import json
import threading
import socket

# Node acting as both client and server

class Node:
    def __init__(self, server_port, nodes_file):
        self.server_port = server_port
        self.nodes = self.load_nodes(nodes_file)
        self.transaction_pool = []
        self.blockchain = [self.create_genesis_block()]

    def load_nodes(self, file_path):
        with open(file_path) as f:
            nodes_list = []
            for line in f.readlines():
                ip, port = line.strip().split(":")
                nodes_list.append((ip, int(port)))
            return nodes_list

    def start_server(self):
        threading.Thread(target=self.run_server).start()
        self.connect_nodes()

    def run_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("", self.port))
        server_socket.listen(5)
        print(f"Listening on port {self.port}")
        while True:
            # Accept incoming connection requests from other nodes
            # Allows this server to handle other clients
            conn, addr = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn,)).start()

    def handle_client(self, conn):  # Server: Handles requests from other clients
        try:
            while True:
                data = recv_prefixed(conn).decode()
                message = json.loads(data)
                if message["type"] == "transaction":
                    self.handle_transaction_request(message["payload"])
                elif message["type"] == "values":
                    self.handle_block_request(message["payload"])
                else:
                    print("Invalid message type!")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            conn.close()

    def handle_transaction_request(self, payload):
        # Transaction: sender, message, nonce, signature
        transaction = Transaction(**payload)
        if transaction.is_valid():
            self.transaction_pool.append(transaction)
            # broadcast transaction

    def handle_block_request(self, index):
        pass

    def connect_nodes(self):
        for ip, port in self.node_list:
            try:
                # Initiate connection with other servers nodes (using their ip, port from file)
                # Allows this client to connect with other servers
                node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                node_socket.connect((ip, port))
                threading.Thread(target=self.listen_to_node, args=(node_socket,)).start()
            except Exception as e:
                print(f"Failed to connect to IP {ip} on port {port}")

    def listen_to_node(self, node_socket):  # Client: Listens for messages from other nodes
        try:
            while True:
                data = recv_prefixed(node_socket).decode()
                message = json.loads(data)
                if isinstance(message, dict) and "response" in message:  # Transaction response
                    self.handle_transaction_response(message["response"])
                elif isinstance(message, list):  # Block response
                    self.handle_block_response(message)
                else:
                    print("Invalid message type!")
        except Exception as e:
            print(f"Error listening to node: {e}")
        finally:
            node_socket.close()

    def handle_transaction_response(self, response):
        pass

    def handle_block_response(self, response):
        pass

    def create_genesis_block(self):
        return Block(0, [], "0" * 64)

    def create_new_block(self, previous_hash=None):
        # Block: index, transactions, previous_hash
        block = Block(
            len(self.blockchain) + 1,
            self.transaction_pool.copy(),
            previous_hash or self.blockchain[-1]["current_hash"]
        )
        self.transaction_pool = []
        self.blockchain.append(block)

