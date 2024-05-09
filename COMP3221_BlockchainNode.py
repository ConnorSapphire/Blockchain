from network import *
from blockchain import Blockchain, validate_message, MessageValidationError

import sys
import json
import threading
from threading import Lock
import socket
import socketserver
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519

# Node acting as both client and server

class NodeServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass, node, bind_and_activate=True):
        # TODO initialize self.blockchain and self.blockchain_lock
        self.node = node
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

class NodeServerHandler(socketserver.BaseRequestHandler):
    server: NodeServer
    
    def handle(self):
        # create an infinite loop with the following steps
        # 1. receive data from the client using recv_prefixed and self.request
        # break to exit the loop in case of exception
        # 2. print the received data
        # 3. add the transaction to blockchain. use self.blockchain_lock to avoid data race
        # 4. send the response to the client using send_prefixed
        while True:
            try:
                data = recv_prefixed(self.request)
            except:
                break
            mess_type = None
            with self.server.node.blockchain_lock:
                # TODO: PRINT RECEIVED A TRANSACTION FOR BOTH VALID AND INVALID TRANSACTIONS HERE
                # print(self.client_address[0])
                valid = isinstance(tx := validate_message(data), dict)
                if valid:
                    mess_type = tx["type"]
                    
                    # process transaction type
                    if mess_type == "transaction":
                        if (tx['sender'] in self.server.node.nonces):
                            valid = tx["nonce"] == self.server.node.nonces[tx['sender']]
                        else:
                            valid = tx["nonce"] == 0
                            self.server.node.nonces[tx['sender']] = 0
                        if valid:    
                            self.server.node.nonces[tx['sender']] += 1
                            tx.pop("type")
                            self.server.node.blockchain.pool.append(tx)
                            print(f"[MEM] Stored transaction in the transaction pool: {tx['signature']}")
                        else:
                            print(f"[TX] Received an invalid transaction, wrong nonce - {tx}")
                            
                    # process block request type
                    elif mess_type == "values":
                        print(f"[BLOCK] Received a block request from node {self.client_address[0]}: {tx['payload']}")
                        if tx['payload'] == len(self.server.node.blockchain.blockchain) and self.client_address not in self.server.node.responses:
                            self.server.node.block_request = True
                        
            # respond to transaction type
            if mess_type == "transaction":
                send_prefixed(self.request, json.dumps({'response': valid}).encode())
                
            # respond to block request type
            elif mess_type == "values" and valid:
                if tx['payload'] < len(self.server.node.blockchain.blockchain):
                    send_prefixed(self.request, json.dumps(self.server.node.blockchain.blockchain[tx['payload']], sort_keys=True).encode())
                elif tx['payload'] == len(self.server.node.blockchain.blockchain):
                    send_prefixed(self.request, json.dumps(self.server.node.blockchain.new_proposal(), sort_keys=True).encode())
                    


class Node:
    def __init__(self, server_port, nodes_file):
        self.server_host = "0.0.0.0"
        self.server_port = server_port
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.sender = self.private_key.public_key().public_bytes_raw().hex()
        self.node_list = self.load_nodes(nodes_file)
        self.nonces = dict()
        self.socks = dict()
        self.block_request = False
        self.responses = dict()
        self.f = ((len(self.node_list) + 1) // 2) - 1
        self.blockchain = Blockchain()
        self.blockchain_lock = Lock()

    def load_nodes(self, file_path: str) -> list[tuple[str,int]]:
        """Generate list of all node ip addresses and ports.

        Args:
            file_path (str): Path to file containing information.

        Returns:
            list[tuple[str, int]]: List of all ip, port connections for nodes
        """
        
        with open(file_path) as f:
            node_list = []
            for line in f.readlines():
                ip, port = line.strip().split(":")
                node_list.append((ip, int(port)))
        return node_list

    # SERVER SIDE
    def start_server(self) -> None:
        """Start the server thread and the client threads.
        """
        
        print("STARTING SERVER...")
        threading.Thread(target=self.run_server).start()
        self.connect_nodes()
        threading.Thread(target=self.consensus).start()

    def run_server(self) -> None:
        """Run the TCP server forever
        """
        
        with NodeServer((self.server_host, self.server_port), NodeServerHandler, self) as server:
            server.serve_forever()

    # CLIENT SIDE
    def connect_nodes(self):
        print("CONNECTING TO NODES...")
        heap = self.node_list.copy()
        # continue attempting to connect to each node
        while len(heap) != 0:
            # connect to first node
            node = heap[0]
            try:
                # initiate connection with other servers nodes (using their ip, port from file)
                node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                node_socket.connect(node)
            except Exception as e:
                print(f"Failed to connect to IP {node[1]} on port {node[0]}")
                print("Trying again...")
                continue
            # remove node from heap if connected
            heap.pop(0)
            # store socket for node
            self.socks[node] = node_socket
            
    def send_transaction(self, sock, transaction):
        send_prefixed(sock, transaction.encode())
        try:
            data = recv_prefixed(sock).decode()
            print(data)
        except Exception as e:
            print(e)
            
    def send_block_request(self, sock):
        for i in range(2):
            request = json.dumps({
                'type': 'values',
                'payload': len(self.blockchain.blockchain)
            }, sort_keys=True)
            send_prefixed(sock, request.encode())
            sock.settimeout(5)
            try:
                data = recv_prefixed(sock).decode()
                
                # TODO
                print("HERE\nHERE\nHERE")
                print(f"DATA DATA DATA {data}")
                
                sock.settimeout(None)
                return data
            except Exception as e:
                print("Connection failed, retrying...")
                continue  

    def handle_block_response(self, response):
        print("BLOCK RESPONSE")
        pass
    
    def consensus(self):
        while True:
            if (len(self.blockchain.pool) > 0 or self.block_request):
                proposal = self.blockchain.new_proposal()
                print(f"[PROPOSAL] Created a block proposal: {proposal}")
                for key in self.socks:
                    if key not in self.responses:
                        self.responses[key] = self.send_block_request(self.socks[key])
                        
                        # remove sockets that aren't responding
                        if self.responses[key] == None:
                            self.socks.pop(key)
                        
                self.block_request = False
                    

    # def create_new_block(self, previous_hash=None):
    #     print("CREATE NEW BLOCK")
    #     # Block: index, transactions, previous_hash
    #     block = Block(
    #         len(self.blockchain) + 1,
    #         self.transaction_pool.copy(),
    #         previous_hash or self.blockchain[-1]["current_hash"]
    #     )
    #     self.transaction_pool = []
    #     self.blockchain.append(block)


if __name__ == "__main__":
    try:
        port = int(sys.argv[1])
        node_list = sys.argv[2]
        node = Node(port, node_list)
        node.start_server()
    except IndexError:
        print("Usage: python COMP3221_BlockchainNode.py <port> <node list file path>")
