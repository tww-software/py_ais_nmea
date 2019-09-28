"""
module to deal with getting NMEA 0183 sentences from the network
"""

import logging
import socket

import nmea

AISLOGGER = logging.getLogger(__name__)


def mpserver(dataqueue, host='127.0.0.1', port=10110):
    """
    listen for and put data onto the queue

    Note:
        This is designed to be run in another thread or process to the main
        program

    Args:
        dataqueue(Queue): queue to put data recieved onto
        host(str): host interface ip to listen on
        port(int): UDP port to listen on
    """
    serversock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serversock.bind((host, port))
    AISLOGGER.info('listening on ip %s port %s', host, port)
    while True:
        data, addr = serversock.recvfrom(1024)
        try:
            decodeddata = data.decode('utf8')
            if data and nmea.NMEASENTENCEREGEX.match(decodeddata):
                dataqueue.put(decodeddata)
        except UnicodeDecodeError:
            continue
