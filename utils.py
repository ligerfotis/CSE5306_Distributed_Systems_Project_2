# Prepare username and header and send them We need to encode username to bytes, then count number of bytes and
# prepare header of fixed size, that we encode to bytes as well
import os
import queue
import socket


def send_msg(socket, message, header_length):
    username = message.encode('utf-8')
    username_header = f"{len(username):<{header_length}}".encode('utf-8')
    socket.send(username_header + username)


# Handles message receiving
def receive_file(client_socket, header_length):
    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(header_length)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or
        # socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script or just
        # lost his connection socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information
        # about closing the socket (shutdown read/write) and that's also a cause when we receive an empty message
        return False


def receive_msg(client_socket, header_length):
    # Receive our "header" containing username length, it's size is defined and constant
    msg_header = client_socket.recv(header_length)

    # Convert header to int value
    message_length = int(msg_header.decode('utf-8').strip())

    # Receive and decode username
    message = client_socket.recv(message_length).decode('utf-8')
    return message


def check_username(username, clients):
    for socket in clients:
        if clients[socket]["data"].decode() == username:
            return False
    return True


def connect_client(ip, port):
    # Create a socket socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH,
    # AF_UNIX socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams,
    # socket.SOCK_RAW - raw IP packets
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to a given ip and port
    client_socket.connect((ip, port))

    # Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
    client_socket.setblocking(False)
    return client_socket


def save_file(text, path, client_file):
    # create dir to store received texts from clients
    if not os.path.exists(path):
        os.mkdir(path)
    # check if file exists already and erase it if so
    if os.path.exists(path + client_file):
        os.remove(path + client_file)

    with open(path + client_file, "wt") as file:
        file.write(text)

