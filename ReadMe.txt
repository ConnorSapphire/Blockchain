Coding Environment:
	Language:
		python version 3.10.0 or higher

	Default Packages:
		sys
		socket
		socketserver
		struct
		threading
		json
		time
		Enum
		hashlib
		re

	Installed Packages:
		pip
		cryptography


Run Program:
	Info:
		This program imitates a blockchain network by providing blockchain nodes which
		act as both clients and servers. These nodes transmit requests and responses
		between each other and perform a consensus to decide on which blocks to append
		to the blockchain.

	Run Server:
		Blockchain Node:
			$ python COMP3221_BlockchainNode.py <PORT> node_list/<PORT>_list.txt

			Where <PORT> refers to the corresponding port for the particular node.
			Note that the <PORT> and <IP> values within the node_list files should
			instead be updated to match the other nodes in the network.


	Run Client (Non-Node):
		Non-node Client:
			$ python client.py <IP> <PORT>

			Where <IP> and <PORT> refer to the IP and port of the blockchain node
			that the client will send transaction requests too.

			A sample client has been provided for testing purposes. It will
			sequentially send out transactions and print out the responses it
			received from blockchain nodes.


Batch Run Files:
    Run.bat:
        Executing Run.bat will launch 2 blockchain nodes (can be modified to add more).
        The <PORT> values will need to be adjusted based on chosen ports.

    Client.bat:
        Executing Client.bat will launch 2 clients who will run the code in client.py.
        This will cause transaction requests to be sent to the blockchain nodes, and
        responses will be printed out in the client's corresponding terminal.


References:
    network.py:
        Code from here was not altered and was provided as part of the assignment.

    COMP3221_BlockchainNode.py, blockchain.py, client.py:
        Code from these files use some tutorial code but with major enhancements and
        modifications to better fit our implementation.

