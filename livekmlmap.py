"""
self updating KML map
"""

import datetime
import logging
import os
import multiprocessing
import shutil
import time

import ais
import kml
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
        self.outputpath = outputpath
        self.mpq = multiprocessing.Queue()
        self.serverprocess = None
        if not os.path.exists(outputpath):
            AISLOGGER.info('output path does not exist creating directories')
            os.makedirs(outputpath)
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
                                self.kmlpath, kmzoutput=False,
                                linestring=False)
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


class AdvancedLiveKMLMap(LiveKMLMap):
    """
    a more advanced live KML map that also shows ship type and heading
    """

    def __init__(self, outputpath):
        super().__init__(outputpath)
        self.copy_icons()

    def copy_icons(self):
        """
        copy icons into the output folder so the kml file can see them
        """
        iconspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'static', 'icons')
        arrowspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  'static', 'green_arrows')
        iconsdestination = os.path.join(self.outputpath, 'icons')
        arrowsdestination = os.path.join(self.outputpath, 'green_arrows')
        if not os.path.exists(iconsdestination):
            shutil.copytree(iconspath, iconsdestination)
        if not os.path.exists(arrowsdestination):
            shutil.copytree(arrowspath, arrowsdestination)

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
                            self.create_detailed_map()
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

    def create_detailed_map(self, aistracker=None):
        """
        created a map with full colour icons

        Args:
            aistracker(ais.AISTracker): ais tracker object if we are calling
                                        this externally and not using the
                                        get_nmea_sentences method
        """
        if not aistracker:
            aistracker = self.aistracker
        if os.path.exists(self.kmlpath):
            os.remove(self.kmlpath)
        kmzoutput = True
        kmlmap = kml.KMLOutputParser(self.kmlpath)
        kmlmap.create_kml_header(kmz=kmzoutput)
        for stn in aistracker.stations_generator():
            try:
                lastpos = stn.get_latest_position()
            except ais.NoSuitablePositionReport:
                continue
            stntype = stn.stntype
            stninfo = stn.get_station_info()
            desc = kmlmap.format_kml_placemark_description(stninfo)
            kmlmap.open_folder(stn.mmsi)
            try:
                heading = lastpos['True Heading']
                if heading != ais.HEADINGUNAVAILABLE:
                    kmlmap.add_kml_placemark(stn.mmsi, desc,
                                             str(lastpos['Longitude']),
                                             str(lastpos['Latitude']),
                                             heading, kmzoutput)
            except KeyError:
                pass
            kmlmap.add_kml_placemark(stn.mmsi, desc,
                                     str(lastpos['Longitude']),
                                     str(lastpos['Latitude']),
                                     stntype, kmzoutput)
            kmlmap.close_folder()
        kmlmap.close_kml_file()
        kmlmap.write_kml_doc_file()
