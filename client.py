import queue
import errno
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
        self.username, self.socket = [None, None]

        # self.username, self.socket = set_up_username(my_username, HEADER_LENGTH)

        with open("mytext.txt", "r") as file:
            text_list = file.readlines()
            self.text_string = ''.join(text_list)

        self.q = queue.Queue()
        self.q.put("hey")
        self.q.put("hi")
        self.q.put("hello")

    def set_up_connection(self, username):
        try:
            self.username, self.socket = set_up_username(username, HEADER_LENGTH)
            return True
        except Exception as e:
            print(e)
            return False

    def main(self):
        start_time = time.time()
        while True:
            if (time.time() - start_time) > 5:
                send_msg(self.socket, self.text_string, HEADER_LENGTH)

                while 1:
                    msg = receive_file(self.socket, header_length=HEADER_LENGTH)
                    if msg:
                        break
                msg = msg["data"].decode()
                path = "client_files/"
                filename = "annotated_txt_{}.txt".format(self.username)
                save_file(msg, path, filename)

                start_time = time.time()

            # polling
            try:
                # Now we want to loop over received messages (there might be more than one) and print them
                while True:

                    # Receive our "header" containing username length, it's size is defined and constant
                    msg_header = self.socket.recv(HEADER_LENGTH)

                    # If we received no data, server gracefully closed a connection, for example using socket.close() or
                    # socket.shutdown(socket.SHUT_RDWR)
                    if not len(msg_header):
                        print('Connection closed by the server')
                        sys.exit()

                    # Convert header to int value
                    message_length = int(msg_header.decode('utf-8').strip())

                    message = self.socket.recv(message_length).decode('utf-8')
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


# client = Client()
# username = input("Username: ")
# client.set_up_connection(username)
# client.main()
