"""
module to deal with getting NMEA 0183 sentences from the network
"""

import datetime
import logging
import os
import socket
import subprocess

import ais
import nmea


AISLOGGER = logging.getLogger(__name__)


def read_from_network(outpath, host='localhost', port=10110):
    """
    read from network traffic

    Args:
        outpath(str): path to save nmea sentences to
        host(str): hostname to listen on default is localhost
        port(int): UDP port to listen on default is 10110
    """
    AISLOGGER.info('reading nmea sentences from network')
    if not os.path.exists(outpath):
        AISLOGGER.info('output path does not exist creating directories')
        os.makedirs(outpath)
    aistracker = ais.AISTracker()
    nmeatracker = nmea.NMEAtracker()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    with open(outpath, 'w') as fout:
        while True:
            data, _ = sock.recvfrom(1024)
            try:
                ascii = data.decode('ascii')
                payload = nmeatracker.process_sentence(ascii)
                if payload:
                    fout.write(ascii)
                    nowts = datetime.datetime.utcnow()
                    aistracker.process_message(payload, nowts)
                    subprocess.run('clear')
                    table = aistracker.create_table_data()
                    for row in table:
                        print('   '.join(row))
            except nmea.NMEAInvalidSentence as err:
                AISLOGGER.debug(str(err))
                continue
            except nmea.NMEACheckSumFailed as err:
                AISLOGGER.debug(str(err))
                continue
            except ais.UnknownMessageType as err:
                AISLOGGER.debug(str(err))
                AISLOGGER.debug('unknown message - %s', data)
                continue
            except ais.InvalidMMSI as err:
                AISLOGGER.debug(str(err))
                continue
            except IndexError:
                AISLOGGER.debug('no data on line')
                continue
            except KeyboardInterrupt:
                AISLOGGER.info('user exited')
                break
