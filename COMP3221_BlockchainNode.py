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
                tx, mess_type = validate_message(data, self.client_address[0])
                valid = isinstance(tx, dict)

                if valid:
                    mess_type = tx["type"]
                    
                    # process transaction type
                    if mess_type == "transaction":
                        if (tx["payload"]["sender"] in self.server.node.nonces):
                            valid = tx["payload"]["nonce"] >= self.server.node.nonces[tx["payload"]["sender"]]
                            self.server.node.nonces[tx["payload"]["sender"]] = tx["payload"]["nonce"] + 1
                        else:
                            valid = tx["payload"]["nonce"] == 0
                            self.server.node.nonces[tx["payload"]["sender"]] = 1

                        if valid:
                            tx.pop("type")
                            self.server.node.blockchain.pool.append(tx)
                            print(f"[MEM] Stored transaction in the transaction pool: {tx['payload']['signature']}")
                        else:
                            print(f"[TX] Received an invalid transaction, wrong nonce - {tx['payload']}")
                            
                    # process block request type
                    elif mess_type == "values":
                        print(f"[BLOCK] Received a block request from node {self.client_address[0]}: {tx['payload']}")
                        if tx['payload'] == len(self.server.node.blockchain.blockchain) and self.client_address not in self.server.node.expecting:
                            self.server.node.block_request = True
                        self.server.node.expecting.discard(self.client_address)
                        
            # respond to transaction type
            if mess_type == "transaction":
                send_prefixed(self.request, json.dumps({'response': valid}).encode())
                
            # respond to block request type
            elif mess_type == "values":
                if valid:
                    if tx['payload'] < len(self.server.node.blockchain.blockchain):
                        send_prefixed(self.request, json.dumps(self.server.node.blockchain.blockchain[tx['payload']],
                                                               sort_keys=True).encode())
                    elif tx['payload'] == len(self.server.node.blockchain.blockchain):
                        proposal = self.server.node.blockchain.new_proposal()
                        print(f"[PROPOSAL] Created a block proposal: {proposal}")
                        #print("\n<=== CURRENT PROPOSALS LIST")
                        #print(self.server.node.blockchain.current_proposals)
                        #print("====>\n")
                        send_prefixed(self.request, json.dumps(proposal).encode())
                        #send_prefixed(self.request, json.dumps(self.server.node.blockchain.current_proposals).encode())
                    else:
                        send_prefixed(self.request, json.dumps([], sort_keys=True).encode())
                else:  # invalid block request, response empty list []
                    send_prefixed(self.request, json.dumps([], sort_keys=True).encode())

                    


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
        self.expecting = set()
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
            peer = heap[0]
            sock = self.connect_node(peer)
            if not sock:
                print(f"Failed to connect to IP {peer[1]} on port {peer[0]}")
                print("Trying again...")
                continue
            # remove node from heap if connected
            heap.pop(0)
            # store socket for node
            self.socks[peer] = sock
            
    def connect_node(self, peer) -> socket.socket | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(peer)
            return sock
        except Exception as e:
            return None
            
    def send_transaction(self, sock, transaction):
        print("SEND TRANSACTION")
        send_prefixed(sock, transaction.encode())
        try:
            data = recv_prefixed(sock).decode()
            print(data)
        except Exception as e:
            print(e)
            
    def send_block_request(self, sock) -> None | dict:

        # add peer to set of nodes we expect a request from
        peer = sock.getpeername()
        self.expecting.add(peer)
        
        # create and send request with timeout
        request = json.dumps({
            'type': 'values',
            'payload': len(self.blockchain.blockchain)
        }).encode()
        try:
            print("Sending block request to " + str(sock.getpeername()))
            send_prefixed(sock, request)
            sock.settimeout(5)
        except Exception as e:
            try:
                sock.close()
            except Exception as e:
                pass
            return self.attempt_reconnection(peer, request)
        
        # attempt to receive a response
        response = self.handle_block_response(sock)
        
        # attempt to reconnect if failed once
        if not response:
            sock.close()
            response = self.attempt_reconnection(peer, request)
        return response
    
    def attempt_reconnection(self, peer, request) -> None | dict:
        sock = self.connect_node(peer)
        if not sock:
            print("Connection failed, node has crashed and won't be contacted anymore.")
        else:
            try:
                send_prefixed(sock, request)
                sock.settimeout(5)
                response = self.handle_block_response(sock)
                self.socks[peer] = sock
                return response
            except Exception as e:
                return None
        

    def handle_block_response(self, sock, retry = True) -> None | dict:
        try:
            data = recv_prefixed(sock).decode()              
            sock.settimeout(None)
            return json.loads(data)
        except Exception as e:
            if retry:
                print("Connection failed, retrying...")
            else:
                print("Connection failed, node has crashed and won't be contacted anymore.")
    
    def consensus(self):
        # 1. Continuously check to see when to start algorithm:
        #   a) transaction added to transaction pool
        #   b) received block request
        # 2. Perform f + 1 iterations of block requests:
        #   a) send block requests to all connected clients
        #   b) disconnect clients that don't respond
        #   c) add all transactions to pool
        # 3. Create new block
        while True:
            if (len(self.blockchain.pool) > 0 or self.block_request):
                self.block_request = True
                print("CONSENSUS STARTING")
                for i in range(self.f + 1):
                    responses = dict()
                    remove = set()
                    # receive responses from clients
                    for key in self.socks:
                        if key not in responses:
                            responses[key] = self.send_block_request(self.socks[key])
                            
                            # remove sockets that aren't responding
                            if responses[key] == None:
                                remove.add(key)
                            else:
                                print(f"[PROPOSAL] Received a block proposal: index: {responses[key]['index']} transactions: {responses[key]['transactions']}")

                    # all responses received
                    if len(remove) == 0:
                        #break
                        pass

                    # remove crashed nodes
                    for key in remove:            
                        sock = self.socks.pop(key)
                        try:
                            sock.close()
                        except:
                            pass
                        responses.pop(key)
                    
                    # handle more than f crashes
                    if len(self.socks) < len(self.node_list) - self.f:
                        print(f"[CONSENSUS] Cannot reach consensus, exiting...")
                        sys.exit()
                        
                    # process responses and add transaction to pool 
                    for key in responses:
                        txs = responses[key]['transactions']
                        for tx in txs:
                            self.blockchain.add_transaction(tx)
                     
                # compute new block  
                self.blockchain.new_block()
                print(f"[CONSENSUS] Appended to the blockchain: {self.blockchain.last_block()['current_hash']}")
                self.blockchain.current_proposals = []
                self.block_request = False

if __name__ == "__main__":
    try:
        port = int(sys.argv[1])
        node_list = sys.argv[2]
        node = Node(port, node_list)
        node.start_server()
    except IndexError:
        print("Usage: python COMP3221_BlockchainNode.py <port> <node list file path>")
