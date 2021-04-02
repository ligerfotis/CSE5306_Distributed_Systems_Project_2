# Prepare username and header and send them We need to encode username to bytes, then count number of bytes and
# prepare header of fixed size, that we encode to bytes as well
import os
import queue
import select
import socket

from utils import send_msg


def receive_msg(client_socket, header_length):
    # Receive our "header" containing username length, it's size is defined and constant
    msg_header = client_socket.recv(header_length)

    # Convert header to int value
    message_length = int(msg_header.decode('utf-8').strip())

    # Receive and decode username
    message = client_socket.recv(message_length).decode('utf-8')
    return message


def spelling_check(file_to_checked, lexicon):
    """
    Checks a file for spelling errors against lexicon.txt.
    ASSUMPTION: There is only one period at the end of each line.
    :param file_to_checked: file to be checked against the lexicon
    :param lexicon: a list of words in the lexicon
    :return: the annotated text string
    """
    # open the lexicon file
    # with open('server_files/{}'.format(lexicon_file)) as lex_file:
    #     lex_array = lex_file.readline().split(" ")

    # open the file to be checked
    with open(file_to_checked) as file:
        text = file.readlines()

    array_checked_text = []
    # array of lower cased lexicon words
    lower_lex_array = [word.lower() for word in lexicon]
    # array of upper cased lexicon words
    upper_lex_array = [word.upper() for word in lexicon]
    # array of first letter upper cased and the rest lower cased lexicon words
    cap_lex_array = [word.capitalize() for word in lower_lex_array]
    for line in text:
        # convert string to array of words while removing periods, commas and next line special chars
        line_array = line.strip("\n.,").split(" ")
        # substitute a word in the word array if it is in the lower/upper/capitalized lexicon word array
        corrected_array = ['[' + word_i + ']'
                           if word_i in lower_lex_array or word_i in upper_lex_array or word_i in cap_lex_array
                           else word_i
                           for word_i in line_array]

        array_checked_text.append(corrected_array)

    # convert word arrays into strings and add period at the end
    string_checked_text = []
    for line in array_checked_text:
        string_checked_text.append(" ".join(line) + '.\n')

    # # write the annotated text to a file
    # checked_file_name = "server_files/checked_text_{}.txt".format(username)
    # with open(checked_file_name, 'w') as chked_file:
    #     chked_file.writelines(string_checked_text)

    return "".join(string_checked_text)


def print_dict_queues(q_dict):
    for q in q_dict.values():
        q_size = q.qsize()
        for _ in range(q_size):
            tmp = q.get()
            print(tmp)
            q.put(tmp)
    return q_dict


def update_lexicon(word_queue_dict, lexicon):
    """
    Returns updated lexicon. Returned lexicon does not include duplicates
    :param word_queue_dict: a dictionary of a queue of words for each user to be added in the lexicon
    :param lexicon: list of words in lexicon
    :return: updated lexicon
    """
    for word_queue in word_queue_dict.values():
        while word_queue.qsize():
            word = word_queue.get()
            if word not in lexicon:
                print("word \'{}\' added in the lexicon".format(word))
                lexicon.append(word)
    return lexicon
