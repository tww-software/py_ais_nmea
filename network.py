"""
module to deal with getting NMEA 0183 sentences from the network
"""

import asyncio
import datetime
import logging
import os
import socket
import subprocess
import multiprocessing
import queue

import ais
import nmea


def mpserver(dataqueue, host = '127.0.0.1', port = 10110):
    """
    listen for NMEA sentences
    """
    serversock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serversock.bind((host, port))
    while True:
        data, addr = serversock.recvfrom(1024)
        if data:
            dataqueue.put(data)
