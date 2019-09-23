"""
module to deal with getting NMEA 0183 sentences from the network
"""

import logging
import socket


AISLOGGER = logging.getLogger(__name__)


def mpserver(dataqueue, host='127.0.0.1', port=10110):
    """
    listen for and put data onto the queue

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
        if data:
            dataqueue.put(data)
