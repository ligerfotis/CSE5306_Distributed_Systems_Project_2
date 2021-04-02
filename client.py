import queue
import errno
import select
import sys
import time

from utils import send_msg, receive_file, save_file, set_up_username

HEADER_LENGTH = 10

"""
Code based on https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/
"""


class Client:
    def __init__(self):
        # my_username = input("Username: ")
        self.send_file_to_server = False
        self.username, self.socket = [None, None]
        self.sockets_list = None

        # self.username, self.socket = set_up_username(my_username, HEADER_LENGTH)

        with open("mytext.txt", "r") as file:
            text_list = file.readlines()
            self.text_string = ''.join(text_list)

        self.q = queue.Queue()
        # self.q.put("hey")
        # self.q.put("hi")
        # self.q.put("hello")

    def set_up_connection(self, username):
        try:
            self.username, self.socket = set_up_username(username, HEADER_LENGTH)
            self.sockets_list = [self.socket]
            return True
        except Exception as e:
            print(e)
            return False

    def main(self):
        start_time = time.time()
        while 1:
            # if time.time() - start_time > 5:
            #     self.exchange_file_with_server()
            #     start_time = time.time()
            try:
                # Now we want to loop over received messages (there might be more than one) and print them
                while True:

                    # Receive our "header" containing username length, it's size is defined and constant
                    msg_header = self.socket.recv(HEADER_LENGTH)
                    print("message header: {}".format(msg_header.decode()))
                    # If we received no data, server gracefully closed a connection, for example using socket.close() or
                    # socket.shutdown(socket.SHUT_RDWR)
                    if not len(msg_header):
                        print('Connection closed by the server')
                        sys.exit()

                    # Convert header to int value
                    message_length = int(msg_header.decode('utf-8').strip())
                    print("message length: {}".format(message_length))

                    message = self.socket.recv(message_length).decode('utf-8')
                    print("message: {}".format(message))

                    if message == "poll":
                        print(message)
                        while not self.q.empty():
                            send_msg(self.socket, self.q.get(), HEADER_LENGTH)
                        send_msg(self.socket, "poll_end", HEADER_LENGTH)

                        self.q.put("hey")
                        self.q.put("hi")
                        self.q.put("hello")

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()
                continue

            except Exception as e:
                print('Reading error: '.format(str(e)))
                sys.exit()

    def main2(self):
        while True:
            # check for polling demand
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list, 0.5)
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
                        print(message)
                        while not self.q.empty():
                            send_msg(self.socket, self.q.get(), HEADER_LENGTH)
                        send_msg(self.socket, "poll_end", HEADER_LENGTH)

                        # self.q.put("hey")
                        # self.q.put("hi")
                        # self.q.put("hello")

            if self.send_file_to_server:
                self.send_file()
                read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
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
                        print(message)
                        # print("received annotated text: \n{}".format(msg))
                        path = "client_files/"
                        filename = "annotated_txt_{}.txt".format(self.username)
                        save_file(message, path, filename)
                        print("finished exchanging")
                        self.send_file_to_server = False

    def send_file(self):
        send_msg(self.socket, self.text_string, HEADER_LENGTH)
        print("text sent to server")

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

# client = Client()
# username = input("Username: ")
# client.set_up_connection(username)
# client.main()
