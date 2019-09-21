"""
self updating KML map
"""

import datetime
import logging
import os
import multiprocessing
import sys

import ais
import network
import nmea

AISLOGGER = logging.getLogger(__name__)


class LiveKMLMap():
    """
    a live map for google earth
    """

    kmlnetlink = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <NetworkLink>
      <name>Live AIS Traffic</name>
      <description>show AIS stations on a map</description>
      <Link>
        <href>{}</href>
        <refreshVisibility>1</refreshVisibility>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>1</refreshInterval>
      </Link>
    </NetworkLink>
</kml>"""

    def __init__(self, outputpath):
        self.mpq = multiprocessing.Queue()
        self.serverprocess = None
        if not os.path.exists(outputpath):
            AISLOGGER.info('output path does not exist creating directories')
            os.makedirs(outpath)
        self.netlinkpath = os.path.join(outputpath, 'netlink.kml')
        self.kmlpath = os.path.join(outputpath, 'livemap.kml')
        self.aistracker = ais.AISTracker()
        self.nmeatracker = nmea.NMEAtracker()

    def create_netlink_file(self):
        """
        write the netlink file
        """
        with open(os.path.join(self.netlinkpath), 'w') as netlinkfile:
            netlinkfile.write(self.kmlnetlink.format(self.kmlpath))

    def start_server(self):
        """
        start listening for sentences
        """
        self.serverprocess = multiprocessing.Process(target=network.mpserver,
                                                     args=[self.mpq])
        self.serverprocess.start()

    def stop_server(self):
        """
        stop the server process
        """
        AISLOGGER.info('stopping server process')
        self.serverprocess.terminate()

    def get_nmea_sentences(self):
        """
        get the nmea sentences from the network and write to kml file
        """
        AISLOGGER.info('live KML map, open {} to track vessels'.format(
            os.path.realpath(self.netlinkpath)))
        while True:
            qdata = self.mpq.get()
            if qdata:
                try:
                    data = qdata.decode('utf-8')
                    payload = self.nmeatracker.process_sentence(data)
                    if payload:
                        currenttime = datetime.datetime.utcnow().strftime(
                            '%Y/%m/%d %H:%M:%S')
                        msg = self.aistracker.process_message(
                            payload, timestamp=currenttime)
                        AISLOGGER.info(msg.__str__())
                        if currenttime.endswith('5'):
                            self.aistracker.create_kml_map(
                                self.kmlpath, kmzoutput=False)
                except (nmea.NMEAInvalidSentence, nmea.NMEACheckSumFailed,
                        ais.UnknownMessageType, ais.InvalidMMSI) as err:
                    AISLOGGER.debug(str(err))
                    continue
                except IndexError:
                    AISLOGGER.debug('no data on line')
                    continue
                except KeyboardInterrupt:
                    self.stop_server()
                    break


if __name__ == '__main__':
    KMLOUTPUT = sys.argv[1]
    LIVEKMLMAP = LiveKMLMap(KMLOUTPUT)
    LIVEKMLMAP.create_netlink_file()
    LIVEKMLMAP.start_server()
    LIVEKMLMAP.get_nmea_sentences()
