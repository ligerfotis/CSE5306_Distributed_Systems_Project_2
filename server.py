import os
import queue
import socket
import select
import time

from utils import send_msg, receive_file, check_username, save_file
from utils_server import q_polling

HEADER_LENGTH = 10
polling_timeout = 10

IP = "127.0.0.1"
PORT = 1234

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))

# Listen to new connections
server_socket.listen()

# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}

print(f'Listening for connections on {IP}:{PORT}...')

start_time = time.time()
while True:

    # Calls Unix select() system call or Windows select() WinSock call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
    #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    # Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send thru them
    #   - errors  - sockets with some exceptions
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    timeout = polling_timeout - (time.time() - start_time)
    # print(timeout)
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list, timeout)
    if not (read_sockets or exception_sockets):
        # print('timed out, do some other work here')
        q_dict = q_polling(clients, HEADER_LENGTH)
        # q_dict = print_dict_queues(q_dict)
        start_time = time.time()

    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            # Accept new connection
            # That gives us new socket - client socket, connected to this given client only, it's unique for that client
            # The other returned object is ip/port set
            client_socket, client_address = server_socket.accept()

            # Client should send his name right away, receive it
            user = receive_file(client_socket, header_length=HEADER_LENGTH)

            # If False - client disconnected before he sent his name
            if user is False:
                continue

            username = user['data'].decode()

            if check_username(username, clients):
                # Add accepted socket to select.select() list
                sockets_list.append(client_socket)
                # Also save username and username header
                clients[client_socket] = user
                send_msg(socket=client_socket, message=username, header_length=HEADER_LENGTH)
                print('Accepted new connection from {}:{}, username: {}'.format(*client_address,
                                                                                user['data'].decode('utf-8')))
            else:
                send_msg(socket=client_socket, message="None", header_length=HEADER_LENGTH)
                print('Rejected new connection from {}:{}. username: {} is already in use by another client'.format(
                    *client_address,
                    user['data'].decode('utf-8')))
                client_socket.close()

        # Else existing socket is sending a message
        else:
            # Receive message
            message = receive_file(notified_socket, header_length=HEADER_LENGTH)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)
                # Remove from our list of users
                del clients[notified_socket]
                continue

            username = clients[notified_socket]["data"].decode()
            path = "server_files/"
            client_file = "file_{}.txt".format(username)
            msg = message["data"].decode("utf-8")
            save_file(msg, path, client_file)

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]
            print(f'Received message from {user["data"].decode("utf-8")}: {msg}')
            print("sending {}".format(msg))
            message = msg.encode('utf-8')
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
            notified_socket.send(message_header + message)

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:
        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)
        # Remove from our list of users
        del clients[notified_socket]
