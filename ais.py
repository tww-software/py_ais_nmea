"""
code relating to the identification and tracking of vessels
also the output of the acquired data into csv json kml etc

contains the main class that represents each AIS station
"""

import collections
import csv
import json
import os

import binary
import geojson
import kml
import maritimeidentifiers
import allmessages


class AISStation():
    """
    represents a single AIS station

    Attributes:
        mmsi(int): Maritime Mobile Station Identifier - uniquely identifies the
                AIS station on the network
        type(str): the main type of station it is classA/B/Base Station etc
        subtype(str): the type of ship or navigation aid
        name(str): the name of the station
        posrep(list): list of dictionaries each item is a position report
        details(dict): extra information about the AIS Station
        flag(str): the country the station is sailing under
        sentmsgs(collections.defaultdict): count of different message types
                                           this station has sent
        lastseen(datetime.datetime): the last datetime this station was seen

    Args:
        mmsi(int): same as above
    """

    def __init__(self, mmsi):
        self.mmsi = mmsi
        self.type = 'Unknown'
        self.subtype = 'Unknown'
        self.name = ''
        self.posrep = []
        self.details = {}
        self.flag = self.identify_flag()
        self.sentmsgs = collections.defaultdict(int)
        self.lastseen = None

    def identify_flag(self):
        """
        try to identify the AIS Station's flag from its MMSI

        Returns:
            flag(str): the country the station sails under
        """
        if (str(self.mmsi).startswith('111') or
                str(self.mmsi).startswith('970') or
                str(self.mmsi).startswith('972') or
                str(self.mmsi).startswith('974')):
            mid = int(str(self.mmsi)[3:6])
        elif (str(self.mmsi).startswith('99') or
              str(self.mmsi).startswith('98')):
            mid = int(str(self.mmsi)[2:5])
        else:
            mid = int(str(self.mmsi)[0:3])
        try:
            flag = maritimeidentifiers.MID[int(mid)]
        except KeyError:
            flag = 'Unknown'
        return flag

    def update_position(self, lat, lon, **kwargs):
        """
        update the position of the AIS Station

        Args:
            lat(float): latitude
            lon(float): longitude
            **kwargs: other postion report information
        """
        if lat == 91.0 or lon == 181.0:
            raise NoSuitablePositionReport('do not have a suitable LAT/LON')
        currentpos = {'Latitude': lat, 'Longitude': lon}
        if kwargs:
            currentpos.update(kwargs)
        self.posrep.append(currentpos)

    def find_station_name_and_subtype(self, msgobj):
        """
        Try to identify the AIS stations name and subtype

        Note:
            The station name is given in message types 5, 19, 21 and 24

        Args:
            msgobj(messages.aismessage.AISMessage): message object
        """
        if isinstance(msgobj, allmessages.MSGTYPES[5]):
            self.subtype = msgobj.shiptype
            self.name = msgobj.name
        elif isinstance(msgobj, allmessages.MSGTYPES[19]):
            self.subtype = msgobj.shiptype
            self.name = msgobj.name
        elif isinstance(msgobj, allmessages.MSGTYPES[21]):
            self.subtype = msgobj.aidtype
            self.name = msgobj.name
        elif isinstance(msgobj, allmessages.MSGTYPES[24]):
            if msgobj.partno == 0:
                self.name = msgobj.name
            if msgobj.partno == 1:
                self.subtype = msgobj.shiptype

    def add_station_information(self, msgobj):
        """
        takes a message object and gets useful information from it

        Note:
            message types 1,2,3,4,9,11,18,19,21 and 27 contain position info

        Args:
            msgobj(messages.aismessage.AISMessage): message object
        """
        self.sentmsgs[msgobj.description] += 1
        posreptypes = [allmessages.MSGTYPES[1],
                       allmessages.MSGTYPES[4],
                       allmessages.MSGTYPES[9],
                       allmessages.MSGTYPES[11],
                       allmessages.MSGTYPES[18],
                       allmessages.MSGTYPES[19],
                       allmessages.MSGTYPES[21],
                       allmessages.MSGTYPES[27]]
        msgtype = type(msgobj)
        if msgtype in posreptypes:
            try:
                posrepdict = msgobj.get_position_data()
            except NotImplementedError:
                posrepdict = {}
            try:
                self.update_position(msgobj.latitude,
                                     msgobj.longitude,
                                     **posrepdict)
            except NoSuitablePositionReport:
                pass
        try:
            self.details.update(msgobj.get_details())
        except NotImplementedError:
            pass

    def get_latest_position(self):
        """
        return the last known position we have for the ais station

        Returns:
            'Unknown'(str): if no posrep found
            self.posrep(dict): last item in self.posrep
        """
        try:
            if not self.posrep:
                return 'Unknown'
            return self.posrep[len(self.posrep) - 1]
        except AttributeError:
            return 'Unknown'

    def determine_station_type(self, msgobj):
        """
        try and determine the type of AIS station based on MMSI and what
        message we recieved from it

        Note:
            message types 4,11,15,16,17,20,22 and 23 are only transmitted by
            Base Stations
            message type 21 is only sent by Navigation Aids
            message types 1,2,3,5 and 27 are only sent by Class A
            message types 18,19 and 24 are only sent by Class B
            message type 9 is only sent by SAR Aircraft

        Args:
            msgobj(messages.aismessage.AISMessage): message object
        """
        if str(self.mmsi).startswith('99'):
            self.type = 'Navigation Aid'
        if str(self.mmsi).startswith('98'):
            self.type = 'Auxiliary craft associated with a parent ship'
            return
        if str(self.mmsi).startswith('970'):
            self.type = 'AIS SART (Search and Rescue Transmitter)'
            return
        if str(self.mmsi).startswith('972'):
            self.type = 'MOB (Man Overboard) device'
            return
        if str(self.mmsi).startswith('974'):
            self.type = 'EPIRB (Emergency Position Indicating Radio Beacon)'
            return
        typesdict = {
            allmessages.MSGTYPES[4]: 'Base Station',
            allmessages.MSGTYPES[11]: 'Base Station',
            allmessages.MSGTYPES[15]: 'Base Station',
            allmessages.MSGTYPES[16]: 'Base Station',
            allmessages.MSGTYPES[20]: 'Base Station',
            allmessages.MSGTYPES[22]: 'Base Station',
            allmessages.MSGTYPES[23]: 'Base Station',
            allmessages.MSGTYPES[21]: 'Navigation Aid',
            allmessages.MSGTYPES[1]: 'Class A',
            allmessages.MSGTYPES[5]: 'Class A',
            allmessages.MSGTYPES[27]: 'Class A',
            allmessages.MSGTYPES[18]: 'Class B',
            allmessages.MSGTYPES[19]: 'Class B',
            allmessages.MSGTYPES[24]: 'Class B',
            allmessages.MSGTYPES[9]: 'SAR Aircraft'}
        msgtype = type(msgobj)
        if msgtype in typesdict:
            self.type = typesdict[msgtype]
            if self.type == 'SAR Aircraft':
                self.subtype = 'SAR Aircraft'
            if self.type == 'Base Station':
                self.subtype = 'Base Station'
        else:
            self.type = 'Unknown'

    def __str__(self):
        lastpos = self.get_latest_position()
        if lastpos == 'Unknown':
            posstr = lastpos
        else:
            try:
                posstr = '{},{}'.format(lastpos['Latitude'],
                                        lastpos['Longitude'])
            except KeyError:
                posstr = 'Unknown'
        if self.lastseen:
            lastseenstr = self.lastseen.strftime('%H:%M:%S')
        else:
            lastseenstr = 'N/A'
        strtext = ('AIS Station - MMSI: {}, Name: {}, Type: {},'
                   ' Subtype: {}, Flag: {}, Last Known Position: {},'
                   ' Last Seen: {}'.format(self.mmsi,
                                           self.name,
                                           self.type,
                                           self.subtype,
                                           self.flag,
                                           posstr,
                                           lastseenstr))
        return strtext

    def __repr__(self):
        reprstr = '{}()'.format(self.__class__.__name__)
        return reprstr


class AISTracker():
    """
    keep track of multiple AIS stations and their messages

    Attributes:
        stations(dict): dictionary to store the AIS Station objects
                        keys are the station MMSI's
        messages(collections.defaultdict): count of the different message types
                                           recieved
        messagesprocessed(int): total count of messages recieved
        timings(list): timings recieved from AIS base stations
    """

    def __init__(self):
        self.stations = {}
        self.messages = collections.defaultdict(int)
        self.messagesprocessed = 0
        self.timings = []

    def __len__(self):
        return len(self.stations)

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

    def process_message(self, data, timestamp=None):
        """
        determine what type of AIS message it is

        Args:
            data(str): full message payload from 1 or more NMEA sentences
            timestamp(datetime.datetime): time this message was recieved

        Raises:
            UnknownMessageType: if the message type is not in the
                                allmessages.MSGTYPES dict

        Returns:
            msgobj(messages.aismessage.AISMessage): the ais message type object
        """
        msgbinary = binary.ais_sentence_payload_binary(data)
        msgtype = binary.decode_sixbit_integer(msgbinary, 0, 6)
        if msgtype in allmessages.MSGTYPES.keys():
            msgobj = allmessages.MSGTYPES[msgtype](msgbinary)
        else:
            raise UnknownMessageType('unknown message type - ' + str(msgtype))
        if msgobj.mmsi == 0:
            return msgobj
        self.messages[allmessages.MSGDESCRIPTIONS[msgtype]] += 1
        self.messagesprocessed += 1
        if msgobj.mmsi not in self.stations:
            newstn = AISStation(msgobj.mmsi)
            newstn.determine_station_type(msgobj)
            self.stations[msgobj.mmsi] = newstn
        if self.stations[msgobj.mmsi].type == 'Unknown':
            self.stations[msgobj.mmsi].determine_station_type(msgobj)
        if (self.stations[msgobj.mmsi].subtype == 'Unknown' or
                self.stations[msgobj.mmsi].name == ''):
            self.stations[msgobj.mmsi].find_station_name_and_subtype(msgobj)
        self.stations[msgobj.mmsi].add_station_information(msgobj)
        if timestamp:
            self.stations[msgobj.mmsi].lastseen = timestamp
        if (isinstance(msgobj, (allmessages.MSGTYPES[4],
                                allmessages.MSGTYPES[11]))):
            if msgobj.timestamp != '0/0/0 - 24:60:60':
                rxtime = msgobj.timestamp
                self.timings.append(rxtime)
        return msgobj

    def get_centre_of_map(self):
        """
        find the centre of the map based on what lat lon positions
        we have recieved

        Returns:
            centre(dict): the centre of the map
        """
        lats = []
        lons = []
        for mmsi in self.stations:
            lastpos = self.stations[mmsi].get_latest_position()
            if lastpos == 'Unknown':
                continue
            lats.append(lastpos['Latitude'])
            lons.append(lastpos['Longitude'])
        centrelat = sorted(lats)[len(lats) // 2]
        centrelon = sorted(lons)[len(lons) // 2]
        centre = {'Latitude': centrelat, 'Longitude': centrelon}
        return centre

    def print_table(self):
        """
        quick method to print all the stations the AISTracker knows
        """
        for mmsi in self.stations:
            print(self.stations[mmsi].__str__())

    def all_station_info(self, verbose=False):
        """
        get all the station information we have in a dictionary

        Args:
            verbose(bool): if true then all positions of vessels that have been
                           recorded will be returned, if false then only the
                           last know position will be returned for each vessel

        Returns:
            allstations(dict): dictionary of all the information the aistracker
                               currently has on all vessels it has recorded
        """
        allstations = {}
        stntypes = []
        subtypes = []
        flags = []
        for mmsi in self.stations:
            allstations[mmsi] = self.stations[mmsi].__dict__.copy()
            allstations[mmsi]['Last Known Position'] = (self.stations[mmsi]
                                                        .get_latest_position())
            stntypes.append(self.stations[mmsi].type)
            subtypes.append(self.stations[mmsi].subtype)
            flags.append(self.stations[mmsi].flag)
            if not verbose:
                try:
                    del allstations[mmsi]['posrep']
                except AttributeError:
                    print('no posrep to delete')
                    continue
        allstations['Total Unique Stations'] = self.__len__()
        allstations['Total Messages Processed'] = self.messagesprocessed
        allstations['Message Stats'] = self.messages
        allstations['AIS Station Types'] = collections.Counter(stntypes)
        allstations['Ship Types'] = collections.Counter(subtypes)
        allstations['Country Flags'] = collections.Counter(flags)
        try:
            allstations['Times'] = {}
            allstations['Times']['Started'] = self.timings[0]
            allstations['Times']['Finished'] = self.timings[ \
                len(self.timings) - 1]
        except IndexError:
            allstations['Times'] = 'No time data available.'
        return allstations

    def create_kml_map(self, outputfile):
        """
        create a KML map of all the vessels we have on record

        Args:
            outputfile(str): full path to output to
        """
        docpath = os.path.join(os.path.dirname(outputfile), 'doc.kml')
        kmlmap = kml.KMLOutputParser(docpath)
        kmlmap.create_kml_header()
        for mmsi in self.stations:
            lastpos = self.stations[mmsi].get_latest_position()
            if lastpos == 'Unknown':
                continue
            else:
                stntype = self.stations[mmsi].subtype
                kmlmap.open_folder(str(mmsi))
                desc = kmlmap.format_kml_placemark_description(
                    self.stations[mmsi].__dict__)
                posreps = self.stations[mmsi].posrep
                kmlmap.add_kml_placemark_linestring(mmsi, posreps)
                kmlmap.add_kml_placemark(mmsi, desc,
                                         str(lastpos['Longitude']),
                                         str(lastpos['Latitude']),
                                         stntype)
                kmlmap.close_folder()
        kmlmap.close_kml_file()
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
        for mmsi in self.stations:
            lastpos = self.stations[mmsi].get_latest_position()
            if lastpos == 'Unknown':
                continue
            else:
                currentmmsi = self.stations[mmsi].mmsi
                currentproperties = {}
                currentproperties['MMSI'] = self.stations[mmsi].mmsi
                currentproperties['Type'] = self.stations[mmsi].type
                currentproperties['Subtype'] = self.stations[mmsi].subtype
                currentproperties['Flag'] = self.stations[mmsi].flag
                currentproperties['Name'] = self.stations[mmsi].name
                currentproperties.update(self.stations[mmsi].details)
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

    def create_csv_data(self):
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
        csvheader = ['MMSI', 'Type', 'Sub Type', 'Flag', 'Name', 'Callsign',
                     'IMO number', 'RAIM', 'Fix Type', 'Position Accuracy',
                     'Latitude', 'Longitude', 'Total Messages']
        csvtable.append(csvheader)
        for mmsi in self.stations:
            line = [mmsi,
                    self.stations[mmsi].type,
                    self.stations[mmsi].subtype,
                    self.stations[mmsi].flag,
                    self.stations[mmsi].name]
            usefulinfo = ['Callsign', 'IMO number',
                          'RAIM in use', 'EPFD Fix type', 'Position Accuracy']
            linedetails = []
            for item in usefulinfo:
                try:
                    linedetails.append(self.stations[mmsi].details[item])
                except KeyError:
                    linedetails.append('')
            line.extend(linedetails)
            lastpos = self.stations[mmsi].get_latest_position()
            if lastpos == 'Unknown':
                lat = ''
                lon = ''
            else:
                lat = lastpos['Latitude']
                lon = lastpos['Longitude']
            totalmsgs = 0
            for i in self.stations[mmsi].sentmsgs:
                totalmsgs += self.stations[mmsi].sentmsgs[i]
            line.append(lat)
            line.append(lon)
            line.append(totalmsgs)
            csvtable.append(line)
        return csvtable


class UnknownMessageType(Exception):
    """
    raise when an unknown AIS message type is encountered
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


def write_csv_file(lines, outpath):
    """
    write out the details to a csv file

    Args:
        lines(list): list of lines to write out to the csv, each line is a list
        outpath(str): full path to write the csv file to
    """
    with open(outpath, 'w') as outfile:
        csvwriter = csv.writer(outfile)
        csvwriter.writerows(lines)
