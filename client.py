import queue
import socket
import select
import errno
import sys
import time

from utils import send_msg, receive_file, connect_client

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = input("Username: ")


client_socket = connect_client(IP, PORT)

send_msg(socket=client_socket, message=my_username, header_length=HEADER_LENGTH)
username = False
while not username:
    username = receive_file(client_socket, header_length=HEADER_LENGTH)
    if username and username["data"].decode() == "None":
        print("username taken")
        client_socket.close()
        my_username = input("Choose another username: ")

        client_socket = connect_client(IP, PORT)
        send_msg(socket=client_socket, message=my_username, header_length=HEADER_LENGTH)
        username = False

username = username["data"].decode()
print("My username is {}".format(username))

file = open("mytext.txt", "r")
text_list = file.readlines()
text_string = ''.join(text_list)

q = queue.Queue()
q.put("hey")
q.put("hi")
q.put("hello")

start_time = time.time()
while True:
    # Wait for user to input a message
    # input("press enter to send file:")
    # message = ""
    # If message is not empty - send it
    if (time.time() - start_time) > 10:
        # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
        message = text_string.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)
        start_time = time.time()

    # polling
    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        while True:

            # Receive our "header" containing username length, it's size is defined and constant
            msg_header = client_socket.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or
            # socket.shutdown(socket.SHUT_RDWR)
            if not len(msg_header):
                print('Connection closed by the server')
                sys.exit()

            # Convert header to int value
            message_length = int(msg_header.decode('utf-8').strip())

            # Receive and decode username
            message = client_socket.recv(message_length).decode('utf-8')
            print(message)
            while not q.empty():
                message = q.get().encode('utf-8')
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                client_socket.send(message_header + message)
            message = "poll_end".encode('utf-8')
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(message_header + message)

            q.put("hey")
            q.put("hi")
            q.put("hello")

    except IOError as e:
        # This is normal on non blocking connections - when there are no incoming data error is going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
        # If we got different error code - something happened
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        print('Reading error: '.format(str(e)))
        sys.exit()
