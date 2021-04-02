import queue
import socket
import select
import time

from utils import send_msg, receive_file, check_username, save_file
from utils_server import update_lexicon, spelling_check, receive_msg

"""
Code based on https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
"""

HEADER_LENGTH = 10
polling_timeout = 60

IP = "127.0.0.1"
PORT = 1234


class Server:
    def __init__(self):

        # Create a socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((IP, PORT))

        # Listen to new connections
        self.socket.listen()

        # List of sockets for select.select()
        self.sockets_list = [self.socket]

        # List of connected clients - socket as a key, user header and name as data
        self.clients = {}

        self.lexicon_list = []
        self.shutdown = False

    def main(self):
        print("Listening for connections on {}:{}...".format(IP, PORT))
        with open("lexicon.txt", "r") as file:
            self.lexicon_list = file.readlines()[0].split(" ")

        start_time = time.time()
        while True:

            timeout = polling_timeout - (time.time() - start_time)
            """
            Polling is based on https://pymotw.com/2/select/
            """
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list, timeout)
            if not (read_sockets or exception_sockets):
                print('timed out, do some other work here')
                q_dict = self.q_polling()
                print("polling finished")
                self.lexicon_list = update_lexicon(q_dict, self.lexicon_list)
                with open("lexicon_updated.txt", "w") as file:
                    file.write(" ".join(self.lexicon_list))
                # q_dict = print_dict_queues(q_dict)
                start_time = time.time()

            # Iterate over notified sockets
            for notified_socket in read_sockets:

                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.socket:

                    # Accept new connection
                    # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                    # The other returned object is ip/port set
                    try:
                        client_socket, client_address = self.socket.accept()
                    except:
                        print("server shut down")
                        self.shutdown = True
                        break
                    # Client should send his name right away, receive it
                    user = receive_file(client_socket, header_length=HEADER_LENGTH)

                    # If False - client disconnected before he sent his name
                    if user is False:
                        continue

                    username = user['data'].decode()

                    if check_username(username, self.clients):
                        # Add accepted socket to select.select() list
                        self.sockets_list.append(client_socket)
                        # Also save username and username header
                        self.clients[client_socket] = user
                        send_msg(socket=client_socket, message=username, header_length=HEADER_LENGTH)
                        print('Accepted new connection from {}:{}, username: {}'.format(*client_address,
                                                                                        user['data'].decode('utf-8')))
                    else:
                        send_msg(socket=client_socket, message="None", header_length=HEADER_LENGTH)
                        print(
                            'Rejected new connection from {}:{}. username: {} is already in use by another client'.format(
                                *client_address,
                                user['data'].decode('utf-8')))
                        client_socket.close()

                # Else existing socket is sending a message
                else:
                    # Receive username
                    message = receive_file(notified_socket, header_length=HEADER_LENGTH)

                    # If False, client disconnected, cleanup
                    if message is False:
                        print(
                            'Closed connection from: {}'.format(self.clients[notified_socket]['data'].decode('utf-8')))
                        # Remove from list for socket.socket()
                        self.sockets_list.remove(notified_socket)
                        # Remove from our list of users
                        del self.clients[notified_socket]
                        continue

                    username = self.clients[notified_socket]["data"].decode()
                    path = "server_files/"
                    client_file = "file_{}.txt".format(username)
                    msg = message["data"].decode("utf-8")
                    save_file(msg, path, client_file)

                    # Get user by notified socket, so we will know who sent the message
                    user = self.clients[notified_socket]
                    print(f'Received message from {user["data"].decode("utf-8")}: {msg}')

                    # annotate misspelled words
                    annotated_text = spelling_check(path + client_file, self.lexicon_list)

                    # print("sending {}".format(annotated_text))
                    send_msg(notified_socket, annotated_text, HEADER_LENGTH)
                    print("finished exchange")

            if self.shutdown:
                break
            self.handle_socket_exceptions(exception_sockets)

    def handle_socket_exceptions(self, exception_sockets):
        # It's not really necessary to have this, but will handle some socket exceptions just in case
        for notified_socket in exception_sockets:
            # Remove from list for socket.socket()
            self.sockets_list.remove(notified_socket)
            # Remove from our list of users
            del self.clients[notified_socket]

    def get_live_usernames(self):
        username_list = []
        for client_socket in self.clients:
            username = self.clients[client_socket]["data"].decode()
            username_list.append(username)
        return username_list

    def q_polling(self):
        polls = {}
        print("polling")
        clients = self.clients.copy()
        for client_socket in clients:
            try:
                # poll each client
                send_msg(client_socket, "poll", HEADER_LENGTH)
                q = queue.Queue()
                while 1:
                    poll_msg = receive_msg(client_socket, HEADER_LENGTH)
                    if poll_msg == 'poll_end':
                        polls[client_socket] = q
                        break
                    else:
                        q.put(poll_msg)
            except select.error:
                print(
                    'Closed connection from: {}'.format(self.clients[client_socket]['data'].decode('utf-8')))
                self.sockets_list.remove(client_socket)
                # Remove from our list of users
                del self.clients[client_socket]
                continue
        return polls

# server = Server()
# server.main()
