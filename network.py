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

import ais
import nmea


def mpserver(mpqueue):
    """
    listen for NMEA sentences
    """
    host = '127.0.0.1'
    port = 10110
    serversock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serversock.bind((host, port))
    while True:
        data, addr = serversock.recvfrom(1024)
        if data:
            mpqueue.put(data)
