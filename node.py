from block import Block

# Node acting as both client and server

class Node:
    def __init__(self, server_port, nodes):
        self.server_port = server_port
        self.nodes = nodes
        self.transaction_pool = []
        self.blockchain = []
        self.create_new_block("0" * 64)

    def start_server(self):
        pass  # Create and start server thread

    def run_server(self):
        pass  # Listen for messages on server port

    def connect_nodes(self):
        pass  # Connect to other nodes in self.nodes

    def send_message(self):
        # Send transaction request
        # Send block request
        pass

    def handle_message(self):
        pass  # Handles message received on server port

    def handle_transaction_request(self):
        # Send transaction request
        # Send block request
        pass

    def handle_block_request(self):
        # Send transaction request
        # Send block request
        pass

    def create_new_block(self, previous_hash=None):
        block = Block(
            len(self.blockchain) + 1,
            self.transaction_pool.copy(),
            previous_hash or self.blockchain[-1]["current_hash"]
        )
        self.transaction_pool = []
        self.blockchain.append(block)

