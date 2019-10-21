"""
code relating to the identification and tracking of vessels
also the output of the acquired data into csv json kml etc

contains the main class that represents each AIS station
"""

import collections
import csv
import json
import os
import re

import binary
import geojson
import icons
import kml
import maritimeidentifiers
import allmessages


SPEEDUNAVAILABLE = 102.3
COGUNAVAILABLE = 360
HEADINGUNAVAILABLE = 511
LATITUDEUNAVAILABLE = 91.0
LONGITUDEUNAVAILABLE = 181.0


class AISStation():
    """
    represents a single AIS station

    Attributes:
        mmsi(str): Maritime Mobile Station Identifier - uniquely identifies the
                   AIS station on the network
        stnclass(str): is the station Class A/B/Base Station etc
        stntype(str): the type of ship or navigation aid
        name(str): the name of the station
        posrep(list): list of dictionaries each item is a position report
        details(dict): extra information about the AIS Station
        flag(str): the country the station is sailing under
        sentmsgs(collections.defaultdict): count of different message types
                                           this station has sent

    Args:
        mmsi(str): same as above
    """

    def __init__(self, mmsi):
        self.mmsi = mmsi
        self.stnclass = 'Unknown'
        self.stntype = 'Unknown'
        self.name = ''
        self.posrep = []
        self.details = {}
        self.flag = self.identify_flag(mmsi)
        self.sentmsgs = collections.Counter()

    @staticmethod
    def identify_flag(mmsi):
        """
        try to identify the AIS Station's flag from its MMSI

        Args:
            mmsi(int): Maritime Mobile Station Identifier
        Returns:
            flag(str): the country the station sails under
        """
        if (mmsi.startswith('111') or
                mmsi.startswith('970') or
                mmsi.startswith('972') or
                mmsi.startswith('974')):
            mid = mmsi[3:6]
        elif (mmsi.startswith('00') or
              mmsi.startswith('99') or
              mmsi.startswith('98')):
            mid = mmsi[2:5]
        elif mmsi.startswith('0'):
            mid = mmsi[1:4]
        else:
            mid = mmsi[0:3]
        try:
            flag = maritimeidentifiers.MID[mid]
        except KeyError:
            flag = 'Unknown'
        return flag

    def update_position(self, currentpos):
        """
        update the position of the AIS Station

        Args:
            currentpos(dict): position report must have a minimum of keys
                              'Latitude' and 'Longitude'

        Raises:
            NoSuitablePositionReport: if we do not have a minimum of a latitude
                                      and longitude in currentpos
        """
        if (currentpos['Latitude'] == LATITUDEUNAVAILABLE or
                currentpos['Longitude'] == LONGITUDEUNAVAILABLE):
            raise NoSuitablePositionReport('do not have a suitable LAT/LON')
        self.posrep.append(currentpos)

    def find_station_name_and_type(self, msgobj):
        """
        Try to identify the AIS stations name and type

        Note:
            The station name is given in message types 5, 19, 21 and 24

        Args:
            msgobj(messages.aismessage.AISMessage): message object
        """
        if msgobj.msgtype == 5 or msgobj.msgtype == 19:
            self.stntype = msgobj.shiptype
            self.name = msgobj.name
        elif msgobj.msgtype == 21:
            self.stntype = msgobj.aidtype
            self.name = msgobj.name
        elif msgobj.msgtype == 24:
            if msgobj.partno == 0:
                self.name = msgobj.name
            if msgobj.partno == 1:
                self.stntype = msgobj.shiptype

    def find_position_information(self, msgobj, timestamp=None):
        """
        takes a message object and gets useful information from it

        Note:
            message types 1,2,3,4,9,11,18,19,21 and 27 contain position info

        Args:
            msgobj(messages.aismessage.AISMessage): message object
        """
        self.sentmsgs[msgobj.description] += 1
        posreptypes = [1, 2, 3, 4, 9, 11, 18, 19, 21, 27]
        if msgobj.msgtype in posreptypes:
            try:
                posrepdict = msgobj.get_position_data()
                if timestamp:
                    posrepdict['Time'] = timestamp
                self.update_position(posrepdict)
            except (NotImplementedError, NoSuitablePositionReport):
                pass
        try:
            self.details.update(msgobj.get_details())
        except NotImplementedError:
            pass

    def get_latest_position(self):
        """
        return the last known position we have for the ais station

        Raises:
            NoSuitablePositionReport: if no posrep found

        Returns:
            self.posrep(dict): last item in self.posrep
        """
        try:
            return self.posrep[len(self.posrep) - 1]
        except (IndexError, AttributeError) as err:
            raise NoSuitablePositionReport('Unknown') from err

    def determine_station_class(self, msgobj):
        """
        try and determine the class of AIS station based on MMSI and what
        message we received from it

        Note:
            message types 4 and 11 are only transmitted by
            Base Stations
            message type 21 is only sent by Navigation Aids
            message types 1,2,3,5 and 27 are only sent by Class A
            message types 14,18,19 and 24 are only sent by Class B
            message type 9 is only sent by SAR Aircraft

        Args:
            msgobj(messages.aismessage.AISMessage): message object
        """
        mmsitypes = {
            '8': 'Portable VHF Transceiver',
            '98': 'Auxiliary craft associated with a parent ship',
            '99': 'Navigation Aid',
            '111': 'SAR Aircraft',
            '970': 'AIS SART (Search and Rescue Transmitter)',
            '972': 'MOB (Man Overboard) device',
            '974': 'EPIRB (Emergency Position Indicating Radio Beacon)'}
        for prefix in mmsitypes:
            if self.mmsi.startswith(prefix):
                self.stnclass = mmsitypes[prefix]
                self.stntype = mmsitypes[prefix]
                return
        typesdict = {
            4: 'Base Station',
            11: 'Base Station',
            21: 'Navigation Aid',
            1: 'A',
            2: 'A',
            3: 'A',
            5: 'A',
            27: 'A',
            14: 'B',
            18: 'B',
            19: 'B',
            24: 'B',
            9: 'SAR Aircraft'}
        if msgobj.msgtype in typesdict:
            self.stnclass = typesdict[msgobj.msgtype]
        if self.stnclass == 'Base Station':
            self.stntype = 'Base Station'

    def get_station_info(self, verbose=False):
        """
        return the most relevant information about this AIS station as a
        dictionary

        Returns:
            stninfo(dict):
        """
        stninfo = {}
        stninfo['MMSI'] = self.mmsi
        stninfo['Class'] = self.stnclass
        stninfo['Type'] = self.stntype
        stninfo['Flag'] = self.flag
        stninfo['Name'] = self.name
        stninfo.update(self.details)
        if verbose:
            stninfo['Position Reports'] = self.posrep
            stninfo['Sent Messages'] = dict(self.sentmsgs)
        else:
            try:
                stninfo['Last Known Position'] = self.get_latest_position()
            except NoSuitablePositionReport:
                stninfo['Last Known Position'] = 'Unknown'
        return stninfo

    def __str__(self):
        strtext = ('AIS Station - MMSI: {}, Name: {}, Class: {},'
                   ' Type: {}, Flag: {}'.format(
                       self.mmsi,
                       self.name,
                       self.stnclass,
                       self.stntype,
                       self.flag))
        return strtext

    def __repr__(self):
        reprstr = '{}()'.format(self.__class__.__name__)
        return reprstr

    def create_kml_map(self, outputfile, kmzoutput=True):
        """
        create a KML map of this stations positions

        Args:
            outputfile(str): full path to output to
            kmzoutput(bool): whether to create a kmz with custom icons (True)
                             or a basic kml file (False)
        """
        if kmzoutput:
            docpath = os.path.join(os.path.dirname(outputfile), 'doc.kml')
        else:
            docpath = os.path.join(outputfile)
        kmlmap = kml.KMLOutputParser(docpath)
        kmlmap.create_kml_header(kmz=kmzoutput)
        stninfo = self.get_station_info()
        kmlmap.open_folder(self.mmsi)
        for pos in self.posrep:
            stninfo['Last Known Position'] = pos
            desc = kmlmap.format_kml_placemark_description(stninfo)
            try:
                heading = pos['True Heading']
                if heading != HEADINGUNAVAILABLE and kmzoutput:
                    kmlmap.add_kml_placemark(self.mmsi, desc,
                                             str(pos['Longitude']),
                                             str(pos['Latitude']),
                                             heading, kmzoutput)
            except KeyError:
                pass
            try:
                kmlmap.add_kml_placemark(self.mmsi, desc,
                                         str(pos['Longitude']),
                                         str(pos['Latitude']),
                                         self.stntype, kmzoutput)
            except KeyError:
                pass
        kmlmap.add_kml_placemark_linestring(self.mmsi, self.posrep)
        kmlmap.close_folder()
        kmlmap.close_kml_file()
        kmlmap.write_kml_doc_file()
        if kmzoutput:
            kml.make_kmz(outputfile)


class AISTracker():
    """
    keep track of multiple AIS stations and their messages

    Attributes:
        stations(dict): dictionary to store the AIS Station objects
                        keys are the station MMSI's
        messages(collections.defaultdict): count of the different message types
                                           recieved
        messagesprocessed(int): total count of messages recieved
        timings(list): timings received from AIS base stations
    """

    def __init__(self):
        self.stations = {}
        self.messages = collections.Counter()
        self.messagesprocessed = 0
        self.timings = []

    def __len__(self):
        return len(self.stations)

    def process_message(self, data, timestamp=None):
        """
        determine what type of AIS message it is

        Note:
            the timestamp can be given as an argument for each message to be
            processed or timings can be approximated from the last type 4/11
            base station report timestamp received. for the latter option it is
            preferred that you have a nearby base station transmitting the
            correct time on a regular interval

        Args:
            data(str): full message payload from 1 or more NMEA sentences
            timestamp(str): time this message was recieved

        Raises:
            UnknownMessageType: if the message type is not in the
                                allmessages.MSGTYPES dict
            InvalidMMSI: if the mmsi = 000000000

        Returns:
            msgobj(messages.aismessage.AISMessage): the ais message type object
        """
        msgbinary = binary.ais_sentence_payload_binary(data)
        msgtype = binary.decode_sixbit_integer(msgbinary[0:6])
        if msgtype in allmessages.MSGTYPES.keys():
            msgobj = allmessages.MSGTYPES[msgtype](msgbinary)
        else:
            raise UnknownMessageType(
                'Unknown message type {} - {}'.format(msgtype, data))
        if msgobj.mmsi == '000000000':
            raise InvalidMMSI('Invalid MMSI - 000000000')
        if msgobj.mmsi not in self.stations:
            self.stations[msgobj.mmsi] = AISStation(msgobj.mmsi)
        if self.stations[msgobj.mmsi].stnclass == 'Unknown':
            self.stations[msgobj.mmsi].determine_station_class(msgobj)
        if (self.stations[msgobj.mmsi].stntype == 'Unknown' or
                self.stations[msgobj.mmsi].name == ''):
            self.stations[msgobj.mmsi].find_station_name_and_type(msgobj)
        if timestamp:
            msgobj.rxtime = timestamp
            if timestamp not in self.timings:
                self.timings.append(timestamp)
        else:
            if msgtype in (4, 11):
                if msgobj.timestamp != '0/00/00 24:60:60':
                    if timestamp not in self.timings:
                        self.timings.append(msgobj.timestamp + ' (estimated)')
            try:
                timestamp = self.timings[len(self.timings) - 1]
            except IndexError:
                timestamp = 'N/A'
        self.stations[msgobj.mmsi].find_position_information(msgobj, timestamp)
        self.messagesprocessed += 1
        self.messages[allmessages.MSGDESCRIPTIONS[msgtype]] += 1
        return msgobj

    def get_centre_of_map(self):
        """
        find the centre of the map based on what lat lon positions
        we have received

        Returns:
            centre(dict): the centre of the map
        """
        lats = []
        lons = []
        for mmsi in self.stations_generator():
            try:
                lastpos = self.stations[mmsi].get_latest_position()
            except NoSuitablePositionReport:
                continue
            lats.append(lastpos['Latitude'])
            lons.append(lastpos['Longitude'])
        centrelat = sorted(lats)[len(lats) // 2]
        centrelon = sorted(lons)[len(lons) // 2]
        centre = {'Latitude': centrelat, 'Longitude': centrelon}
        return centre

    def stations_generator(self):
        """
        a generator because we often find ourselves iterating over the
        self.stations dictionary

        Yields:
            stn(AISStation): ais station object
        """
        for stn in self.stations:
            yield stn

    def tracker_stats(self):
        """
        calculate statistics for this tracker object and return them
        in a dictionary

        Returns:
            stats(dict): various statistics including what types, subtypes,
                         flags and messages we have seen
        """
        stats = {}

        flagcount = collections.Counter()
        stnclasscount = collections.Counter()
        stntypescount = collections.Counter()
        for mmsi in self.stations_generator():
            stnclasscount[self.stations[mmsi].stnclass] += 1
            stntypescount[self.stations[mmsi].stntype] += 1
            flagcount[self.stations[mmsi].flag] += 1
        stats['Total Unique Stations'] = self.__len__()
        stats['Total Messages Processed'] = \
            self.messagesprocessed
        stats['Message Stats'] = self.messages
        stats['AIS Station Types'] = \
            stnclasscount
        stats['Ship Types'] = \
            stntypescount
        stats['Country Flags'] = \
            flagcount
        try:
            stats['Times'] = {}
            stats['Times']['Started'] = self.timings[0]
            stats['Times']['Finished'] = self.timings[
                len(self.timings) - 1]
        except IndexError:
            stats['Times'] = 'No time data available.'
        return stats

    def all_station_info(self, verbose=True):
        """
        get all the station information we have in a dictionary

        Args:
            verbose(bool): equates directly to the verbose argument for
                           the AISStation.get_station_info method

        Returns:
            allstations(dict): dictionary of all the information the aistracker
                               currently has on all vessels it has recorded
        """
        allstations = {}
        for mmsi in self.stations_generator():
            allstations[mmsi] = self.stations[mmsi].get_station_info(
                verbose=verbose)
        return allstations

    def sort_mmsi_by_catagory(self):
        """
        sort MMSIs by type, subtype, flag etc
        so its easy to find all the MMSIs that fall under a certain catagory
        e.g. all the vessels that are Tugs

        Returns:
            organised(dict): dictionary with lists of MMSIs for each catagory
        """
        organised = {}
        stnclasses = collections.defaultdict(list)
        stntypes = collections.defaultdict(list)
        flags = collections.defaultdict(list)
        for mmsi in self.stations_generator():
            stnclasses[self.stations[mmsi].stnclass].append(mmsi)
            stntypes[self.stations[mmsi].stntype].append(mmsi)
            flags[self.stations[mmsi].flag].append(mmsi)
        organised['Flags'] = flags
        organised['Class'] = stnclasses
        organised['Types'] = stntypes
        return organised

    def create_kml_map(self, outputfile, kmzoutput=True):
        """
        create a KML map of all the vessels we have on record

        Args:
            outputfile(str): full path to output to
            kmzoutput(bool): whether to create a kmz with custom icons (True)
                             or a basic kml file (False)
        """
        if kmzoutput:
            docpath = os.path.join(os.path.dirname(outputfile), 'doc.kml')
        else:
            docpath = os.path.join(outputfile)
        kmlmap = kml.KMLOutputParser(docpath)
        kmlmap.create_kml_header(kmz=kmzoutput)
        for mmsi in self.stations_generator():
            try:
                lastpos = self.stations[mmsi].get_latest_position()
            except NoSuitablePositionReport:
                continue
            stntype = self.stations[mmsi].stntype
            stninfo = self.stations[mmsi].get_station_info()
            desc = kmlmap.format_kml_placemark_description(stninfo)
            kmlmap.open_folder(mmsi)
            try:
                heading = lastpos['True Heading']
                if heading != HEADINGUNAVAILABLE and kmzoutput:
                    kmlmap.add_kml_placemark(mmsi, desc,
                                             str(lastpos['Longitude']),
                                             str(lastpos['Latitude']),
                                             heading, kmzoutput)
            except KeyError:
                pass
            posreps = self.stations[mmsi].posrep
            kmlmap.add_kml_placemark_linestring(mmsi, posreps)
            kmlmap.add_kml_placemark(mmsi, desc,
                                     str(lastpos['Longitude']),
                                     str(lastpos['Latitude']),
                                     stntype, kmzoutput)
            kmlmap.close_folder()
        kmlmap.close_kml_file()
        kmlmap.write_kml_doc_file()
        if kmzoutput:
            kml.make_kmz(outputfile)

    def create_geojson_map(self, outputfile=None):
        """
        create a GeoJSON map of all the vessels we have on record

        Args:
            outputfile(str): full path to output to

        Returns:
            geojsonmap(geojson.GeoJsonParser): the geojsonparser object that
                                               can be used for further
                                               processing
        """
        geojsonmap = geojson.GeoJsonParser()
        for mmsi in self.stations_generator():
            try:
                lastpos = self.stations[mmsi].get_latest_position()
            except NoSuitablePositionReport:
                continue
            currentmmsi = self.stations[mmsi].mmsi
            currentproperties = {}
            currentproperties.update(
                self.stations[mmsi].get_station_info())
            currentproperties['Icon'] = \
                icons.ICONS[self.stations[mmsi].stntype]
            try:
                currentproperties['Heading'] = lastpos['True Heading']
            except KeyError:
                currentproperties['Heading'] = HEADINGUNAVAILABLE
            lastlat = lastpos['Latitude']
            lastlon = lastpos['Longitude']
            currentcoords = []
            for pos in self.stations[mmsi].posrep:
                currentcoords.append([pos['Longitude'], pos['Latitude']])
            geojsonmap.add_station_info(currentmmsi,
                                        currentproperties,
                                        currentcoords,
                                        lastlon,
                                        lastlat)
        if outputfile:
            geojsonmap.save_to_file(outputfile)
        return geojsonmap

    def create_table_data(self):
        """
        creates a table of data we have on all vessels

        Note:
            this is a list of lists meant for output to a csv file
            use the function write_csv_file to do this

        Returns:
            csvtable(list): (lists of lists) each list is a line
                            in the csv file
        """
        csvtable = []
        csvheader = ['MMSI', 'Class', 'Type', 'Flag', 'Name', 'Callsign',
                     'IMO number', 'RAIM in use', 'EPFD Fix type',
                     'Position Accuracy', 'Total Messages', 'Latitude',
                     'Longitude', 'CoG', 'Speed (knots)', 'Navigation Status',
                     'Time', 'Destination', 'ETA']
        lastposheader = ['Latitude', 'Longitude', 'CoG', 'Speed (knots)',
                         'Navigation Status', 'Time']
        csvtable.append(csvheader)
        for mmsi in self.stations_generator():
            stninfo = self.stations[mmsi].get_station_info()
            line = []
            stninfo['Total Messages'] = 0
            for i in self.stations[mmsi].sentmsgs:
                stninfo['Total Messages'] += self.stations[mmsi].sentmsgs[i]
            for item in lastposheader:
                try:
                    stninfo[item] = (stninfo['Last Known Position'][item])
                except (NoSuitablePositionReport, TypeError, KeyError):
                    stninfo[item] = ''
            for item in csvheader:
                try:
                    line.append(stninfo[item])
                except KeyError:
                    line.append('')
            csvtable.append(line)
        return csvtable

    def __str__(self):
        try:
            times = 'from {} to {}'.format(
                self.timings[0],
                self.timings[len(self.timings) - 1])
        except IndexError:
            times = 'No time data available.'
        strtext = ('AIS Tracker - tracking {} vessels'
                   ' , processed {} messages,'
                   ' {}'
                   '').format(str(self.__len__()),
                              str(self.messagesprocessed),
                              times)
        return strtext

    def __repr__(self):
        reprstr = '{}()'.format(self.__class__.__name__)
        return reprstr


class UnknownMessageType(Exception):
    """
    raise when an unknown AIS message type is encountered
    """
    pass


class InvalidMMSI(Exception):
    """
    raise when an incorrect MMSI is encountered
    """
    pass


class NoSuitablePositionReport(Exception):
    """
    raise if we cannot get a position
    """
    pass


def write_json_file(jsonstations, outpath):
    """
    write jsonstations to a json file

    Args:
        jsonstations(dict): data to be written to json file
        outpath(str): full path to write to
    """
    with open(outpath, 'w') as jsonfile:
        json.dump(jsonstations, jsonfile, indent=2)


def write_json_lines(datalist, outpath):
    """
    take a list of dictionaries and write them out to a JSON lines file

    Note:
        JSON lines is a text file where each new line is a separate JSON string

    Args:
        datalist(list): a list of dictionaries to write out
        outpath(str): the full filepath to write to
    """
    with open(outpath, 'w') as jsonlines:
        for jdict in datalist:
            jsonlines.write(json.dumps(jdict) + '\n')


def write_csv_file(lines, outpath, dialect='excel'):
    """
    write out the details to a csv file

    Note:
        default dialect is 'excel' to create a CSV file
        we change this to 'excel-tab' for TSV output

    Args:
        lines(list): list of lines to write out to the csv, each line is a list
        outpath(str): full path to write the csv file to
        dialect(str): type of seperated values file we are creating
    """
    with open(outpath, 'w') as outfile:
        csvwriter = csv.writer(outfile, dialect=dialect)
        csvwriter.writerows(lines)


def check_imo_number(imo):
    """
    do a basic integrity check of an IMO number

    Args:
        imo(str): the IMO number as a string

    Returns:
        True: if valid IMO number
        False: invalid IMO number
    """
    if len(imo) > 7:
        return False
    try:
        lastdigit = imo[6]
        total = 0
        multiplyby = 7
        for digit in range(0, 6):
            total += int(imo[digit]) * multiplyby
            multiplyby -= 1
    except IndexError:
        return False
    return bool(str(total)[len(str(total)) - 1] == lastdigit)


def create_summary_text(summary):
    """
    format a dictionary so it can be printed to screen or written to a plain
    text file

    Args:
        summary(dict): the data to format

    Returns:
        textsummary(str): the summary dict formatted as a string
    """
    summaryjson = json.dumps(summary, indent=3)
    textsummary = re.sub('[{},"]', '', summaryjson)
    return textsummary
