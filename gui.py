"""
@author: Fotios Lygerakis
@UTA ID: 1001774373
"""
import socket
import threading
import PySimpleGUI as sg
from client import Client
from utils_gui import server_layout, client_layout, delete_output
from server import Server

"""
Code based on https://pysimplegui.readthedocs.io/en/latest/cookbook/
"""


class GUI:
    def __init__(self, name):
        self.server, self.client = None, None
        if name == "Client":
            self.is_client = True
            self.is_server = False
        else:
            self.is_client = False
            self.is_server = True
        # chose the appropriate layout for the server and the client
        if self.is_server:
            self.layout = server_layout
            self.server = Server()
        elif self.is_client:
            self.layout = client_layout
            self.client = Client()
        self.logged_in = False

        # create a window
        self.window = sg.Window(name, self.layout)

    def run(self):
        """
        Function for handling the GUI
        """

        while True:
            # read the events on the gui and their values
            event, values = self.window.read()
            # exit gui when window is closed or Exit button is pressed
            if event == sg.WIN_CLOSED or event == 'Exit':
                # delete server's layout components
                if self.is_server:
                    delete_output(is_server=self.is_server, layout_used=self.layout)
                    self.server.socket.shutdown(socket.SHUT_RD)
                else:
                    self.client.socket.shutdown(socket.SHUT_RD)
                break

            # Client's gui
            if self.is_client:
                # on submit button take the username that has been entered
                if event == 'Login':
                    # try to log in with the given username
                    print("Trying to log in: {}".format(values[0]))
                    self.logged_in = self.client.set_up_connection(values[0])
                    if self.logged_in:
                        print('You are logged in')
                        thread = threading.Thread(target=self.client.main2)
                        thread.start()
                    else:
                        print("Could not login")

                elif event == "Send Text":
                    self.client.send_file_to_server = True
                    # thread = threading.Thread(target=self.host.exchange_file_with_server)
                    # thread.start()
                    # thread = threading.Thread(target=self.host.exchange_file_with_server)
                    # thread.start()

                elif event == "Add":
                    self.client.add_to_queue(values[1])
            # Server's gui
            elif self.is_server:
                # start a thread for the server when the Go button is pressed
                if event == 'Go':
                    # deactivate Go button
                    self.window.FindElement('Go').Update(disabled=True)
                    thread = threading.Thread(target=self.server.main)
                    thread.start()
                # when "Client List" button is pressed the online usernames are being printed on the gui
                elif event == 'Client List':
                    print("Client List Online: {}".format(self.server.get_live_usernames()))
                # otherwise print the values in the gui
                else:
                    print(values)
        self.window.close()


