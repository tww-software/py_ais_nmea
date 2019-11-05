"""
module to deal with getting NMEA 0183 sentences from the network
"""

import logging
import logging.handlers
import socket

import nmea

AISLOGGER = logging.getLogger(__name__)
SENTENCELOGGER = logging.getLogger('sentences')


def network_send(sentence, rhost, rport):
    """
    send a sentence across the network

    Args:
        sentence(bytes): sentence to send - ASCII encoded bytes
        rhost(str): ip or hostname of the server we want to send to
        rport(int): port of the remote server
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(sentence, (rhost, rport))


def setup_logger(outputpath):
    """
    setup the logger to save NMEA sentences to a file

    Args:
        outputpath(str): path to save to
    """
    logformatstr = '%(message)s'
    logformatter = logging.Formatter(fmt=logformatstr)
    rotatinghandler = logging.handlers.RotatingFileHandler(
        outputpath, maxBytes=1000000)
    rotatinghandler.setFormatter(logformatter)
    SENTENCELOGGER.addHandler(rotatinghandler)
    SENTENCELOGGER.propagate = False
    AISLOGGER.info('saving NMEA sentences to %s', outputpath)


def mpserver(dataqueue, host='127.0.0.1', port=10110,
             remotehost=None, remoteport=None, logpath=None):
    """
    listen for and put data onto the queue
    can also forward sentences to a remote server if specified

    Note:
        This is designed to be run in another thread or process to the main
        program

    Args:
        dataqueue(Queue): queue to put data recieved onto
        host(str): host interface ip to listen on
        port(int): UDP port to listen on
        remotehost(str): ip of server to forward NMEA sentences to
        remoteport(int): port of remote server
        logpath(str): full file path to save nmea logs to
    """
    serversock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serversock.bind((host, port))
    AISLOGGER.info('listening on ip %s port %s', host, port)
    if logpath and logpath != '':
        setup_logger(logpath)
    while True:
        data, addr = serversock.recvfrom(1024)
        try:
            if data:
                decodeddata = data.decode('utf-8')
                multi = nmea.NMEASENTENCEREGEX.findall(decodeddata)
                for part in multi:
                    dataqueue.put(part)
                    if logpath:
                        SENTENCELOGGER.info(part)
                    if remotehost and remoteport:
                        network_send(data, remotehost, remoteport)
        except UnicodeDecodeError:
            continue
