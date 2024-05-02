
# Node acting as both client and server

class Node:
    def __init__(self, server_port, nodes):
        self.server_port = server_port
        self.nodes = nodes
        self.transactions = []
        self.blockchain = []

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

