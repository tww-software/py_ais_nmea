"""
module to deal with getting NMEA 0183 sentences from the network
"""

import asyncio
import datetime
import logging
import os
import socket
import subprocess

import ais
import nmea


AISLOGGER = logging.getLogger(__name__)


class AsyncUDPServer:

    def __init__(self):
        self.aistracker = ais.AISTracker()
        self.nmeatracker = nmea.NMEAtracker()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        self.process_message(message)

    def process_message(self, message):
            try:
                payload = self.nmeatracker.process_sentence(message)
                if payload:
                    nowts = datetime.datetime.utcnow()
                    self.aistracker.process_message(payload, nowts)
                    subprocess.run('clear')
                    table = self.aistracker.create_table_data()
                    for row in table:
                        print(' '.join(row))
            except nmea.NMEAInvalidSentence as err:
                AISLOGGER.debug(str(err))
            except nmea.NMEACheckSumFailed as err:
                AISLOGGER.debug(str(err))
            except ais.UnknownMessageType as err:
                AISLOGGER.debug(str(err))
                AISLOGGER.debug('unknown message - %s', data)
            except ais.InvalidMMSI as err:
                AISLOGGER.debug(str(err))
            except IndexError:
                AISLOGGER.debug('no data on line')   


def start_server(host='localhost', port=10110):
    """
    """
    loop = asyncio.get_event_loop()
    print("Starting UDP server")
    # One protocol instance will be created to serve all client requests
    listen = loop.create_datagram_endpoint(
        AsyncUDPServer, local_addr=(host, port))
    transport, protocol = loop.run_until_complete(listen)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    transport.close()
    loop.close()


if __name__ == '__main__':
    start_server()
