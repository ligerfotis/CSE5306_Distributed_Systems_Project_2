import os
import queue
import select

from utils.utils import send_msg, receive_file, save_file, set_up_username

HEADER_LENGTH = 10

"""
Code based on https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/
"""


class Client:
    def __init__(self):
        self.send_file_to_server = False

        # the username and connection socket
        self.username, self.socket = [None, None]

        # the name of the file to send to the server for checking
        self.filename = None

        # the text retrieved from the file in string format
        self.text_string = None

        # the queue to store the lexicon additions
        self.q = queue.Queue()

    def set_up_connection(self, username):
        try:
            # set up the connection and establish a username to the server
            response = set_up_username(username, HEADER_LENGTH)
            if response is not None:
                self.username, self.socket = response
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def main(self):
        while True:
            # check for polling demand
            read_sockets, _, exception_sockets = select.select([self.socket], [], [self.socket], 0.5)
            # Iterate over notified sockets
            for notified_socket in read_sockets:
                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.socket:
                    # Receive message
                    message = receive_file(notified_socket, header_length=HEADER_LENGTH)
                    # If False, client disconnected, cleanup
                    if message is False:
                        print("False")
                    message = message["data"].decode()
                    if message == "poll":
                        print("A poll is received from the server...")
                        while not self.q.empty():
                            word = self.q.get()
                            send_msg(self.socket, word, HEADER_LENGTH)
                            print("The word \'{}\' was retrieved by the server.".format(word))
                        send_msg(self.socket, "poll_end", HEADER_LENGTH)

            if self.send_file_to_server:
                response = self.send_file()
                # in case file requested does not exist
                if not response:
                    self.send_file_to_server = False
                    continue
                print("Successfully uploaded file to the server.")
                read_sockets, _, exception_sockets = select.select([self.socket], [], [self.socket])
                # Iterate over notified sockets
                for notified_socket in read_sockets:
                    # If notified socket is a server socket - new connection, accept it
                    if notified_socket == self.socket:
                        # Receive message
                        message = receive_file(notified_socket, header_length=HEADER_LENGTH)

                        # If False, client disconnected, cleanup
                        if message is False:
                            print("False")
                        message = message["data"].decode()
                        # print(message)
                        # print("received annotated text: \n{}".format(msg))
                        path = "client_files/"
                        filename = "annotated_{}_{}.txt".format(self.filename, self.username)
                        save_file(message, path, filename)
                        print("The spell check sequence has been completed.")
                        self.send_file_to_server = False

    def send_file(self):
        if os.path.isfile("client_files/" + self.filename):
            with open("client_files/" + self.filename, "r") as file:
                text_list = file.readlines()
                self.text_string = ''.join(text_list)
            send_msg(self.socket, self.text_string, HEADER_LENGTH)
            # print("text sent to server")
            return True
        else:
            print("\'{}\' does not exist.\nPlease provide a valid file name.".format(self.filename))
            return False

    def exchange_file_with_server(self):
        self.send_file()
        msg = False
        while True:
            # Receive message
            msg = receive_file(self.socket, header_length=HEADER_LENGTH)
            if msg:
                break

        msg = msg["data"].decode()
        # print("received annotated text: \n{}".format(msg))
        path = "client_files/"
        filename = "annotated_txt_{}.txt".format(self.username)
        save_file(msg, path, filename)
        print("finished exchanging")

    def add_to_queue(self, word):
        self.q.put(word)
        print("word \'{}\' added in clients queue".format(word))
