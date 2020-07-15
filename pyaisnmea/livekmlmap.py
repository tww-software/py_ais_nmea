"""
self updating KML map
"""

import datetime
import logging
import os
import multiprocessing
import shutil
import time

import pyaisnmea.ais as ais
import pyaisnmea.network as network
import pyaisnmea.nmea as nmea

AISLOGGER = logging.getLogger(__name__)


class LiveKMLMap():
    """
    a live map for google earth

    Args:
        outputpath(str): path to directory to write files to
        kmzoutput(bool): if true then full colour icons are used

    Attributes:
        kmlnetlink(str): the KML for a netlink file
        kmzoutput(bool): output KMZ file?
        mpq(multiprocessing.Queue): queue to get sentences from
        serverprocess(None): placeholder for a multiprocessing.Process object
        netlinkpath(str): path to write the KML netlink file
        kmlpath(str): path to write the actual KML map data to
        logpath(str): path to write the received NMEA sentences to
        aistracker(ais.AISTracker): AIS tracker object to handle the stations
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

    def __init__(self, outputpath, kmzoutput=False):
        self.kmzoutput = kmzoutput
        self.outputpath = outputpath
        self.mpq = multiprocessing.Queue()
        self.serverprocess = None
        if not os.path.exists(outputpath):
            AISLOGGER.info('output path does not exist creating directories')
            os.makedirs(outputpath)
        self.netlinkpath = os.path.join(outputpath, 'open_this.kml')
        self.kmlpath = os.path.join(outputpath, 'livemapdata.kml')
        self.logpath = os.path.join(outputpath, 'nmea-sentence-log.txt')
        self.aistracker = ais.AISTracker()
        self.nmeatracker = nmea.NMEAtracker()
        if kmzoutput:
            self.copy_icons()

    def copy_icons(self):
        """
        copy icons into the output folder so the kml file can see them
        """
        iconspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'static', 'icons')
        greenarrowspath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'static', 'green_arrows')
        orangearrowspath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'static', 'orange_arrows')
        iconsdestination = os.path.join(self.outputpath, 'icons')
        greenarrowsdestination = os.path.join(self.outputpath, 'green_arrows')
        orangearrowsdestination = os.path.join(
            self.outputpath, 'orange_arrows')
        if not os.path.exists(iconsdestination):
            shutil.copytree(iconspath, iconsdestination)
        if not os.path.exists(greenarrowsdestination):
            shutil.copytree(greenarrowspath, greenarrowsdestination)
        if not os.path.exists(orangearrowsdestination):
            shutil.copytree(orangearrowspath, orangearrowsdestination)

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
        self.serverprocess = multiprocessing.Process(
            target=network.mpserver, args=[self.mpq],
            kwargs={'logpath': self.logpath})
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
        AISLOGGER.info('live KML map, open %s to track vessels',
                       os.path.realpath(self.netlinkpath))
        while True:
            qdata = self.mpq.get()
            if qdata:
                try:
                    payload = self.nmeatracker.process_sentence(qdata)
                    if payload:
                        currenttime = datetime.datetime.utcnow().strftime(
                            '%Y/%m/%d %H:%M:%S')
                        msg = self.aistracker.process_message(
                            payload, timestamp=currenttime)
                        AISLOGGER.info(msg.__str__())
                        if currenttime.endswith('5'):
                            self.aistracker.create_kml_map(
                                self.kmlpath, kmzoutput=self.kmzoutput,
                                linestring=False, livemap=True)
                            time.sleep(1)
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
