"""
code relating to the identification and tracking of vessels

contains the main class that represents each AIS station
"""

import collections
import datetime
import os
import re

import pyaisnmea.binary as binary
import pyaisnmea.export as export
import pyaisnmea.geojson as geojson
import pyaisnmea.icons as icons
import pyaisnmea.kml as kml
import pyaisnmea.maritimeidentifiers as maritimeidentifiers
import pyaisnmea.allmessages as allmessages


SPEEDUNAVAILABLE = 102.3
COGUNAVAILABLE = 360
HEADINGUNAVAILABLE = 511
LATITUDEUNAVAILABLE = 91.0
LONGITUDEUNAVAILABLE = 181.0
TIMEUNAVAILABLE = '0/00/00 24:60:60'


TIMEREGEX = re.compile(r'(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])')


NAVHEADERS = ['MMSI', 'Name', 'Callsign', 'Type', 'Flag',
              'Latitude', 'Longitude', 'CoG', 'Speed (knots)',
              'Navigation Status', 'Turn Rate',
              'Time', 'Destination', 'ETA']


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
        binarymsgs(list): list of dictionaries - all the type 6 & 8 binary
                          messages we have from this station
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
        self.binarymsgs = []
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
        elif msgobj.msgtype == 9:
            self.stntype = 'SAR Aircraft'
        elif msgobj.msgtype == 21:
            self.stntype = msgobj.aidtype
            self.name = msgobj.name
        elif msgobj.msgtype == 24:
            if msgobj.partno == 0:
                self.name = msgobj.name
            if msgobj.partno == 1:
                self.stntype = msgobj.shiptype

    def find_position_information(self, msgobj):
        """
        takes a message object and gets useful information from it

        Note:
            message types 1,2,3,4,9,11,18,19,21 and 27 contain position info

        Args:
            msgobj(messages.aismessage.AISMessage): message object
        """
        self.sentmsgs[msgobj.description] += 1
        binarymsgtypes = [6, 8]
        posreptypes = [1, 2, 3, 4, 9, 11, 18, 19, 21, 27]
        if msgobj.msgtype in posreptypes:
            try:
                posrepdict = msgobj.get_position_data()
                self.update_position(posrepdict)
            except (NotImplementedError, NoSuitablePositionReport):
                pass
        try:
            msgdetails = msgobj.get_details()
            if msgobj.msgtype in binarymsgtypes:
                latest = {
                    msgdetails['Binary Message Sub Type']:
                    msgdetails['Details']}
                self.details.update(latest)
                self.binarymsgs.append(msgdetails)
            else:
                self.details.update(msgdetails)
        except NotImplementedError:
            pass

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
        try:
            currentpos['Destination'] = self.details['Destination']
        except KeyError:
            pass
        try:
            currentpos['ETA'] = self.details['ETA']
        except KeyError:
            pass
        self.posrep.append(currentpos)

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

    def get_station_info(self, verbose=False, messagetally=True):
        """
        return the most relevant information about this AIS station as a
        dictionary

        Args:
            verbose(bool): output positions and binary messages
            messagetally(bool): output a tally of the messages types

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
        if messagetally:
            stninfo['Sent Messages'] = dict(self.sentmsgs)
        if verbose:
            stninfo['Position Reports'] = self.posrep
            if self.binarymsgs:
                stninfo['Binary Messages'] = self.binarymsgs
        else:
            try:
                stninfo['Last Known Position'] = self.get_latest_position()
            except NoSuitablePositionReport:
                stninfo['Last Known Position'] = 'Unknown'
        return stninfo

    def create_positions_csv(self, outputfile, dialect='excel'):
        """
        create a CSV file of all the position reports for this station

        Args:
            outputfile(str): path to output CSV file to
            dialect(str): excel for CSV, excel-tab for TSV
        """
        positionlines = []
        stndata = [self.mmsi, self.name, self.stnclass,
                   self.stntype, self.flag]
        header = ['Time', 'Latitude', 'Longitude', 'CoG',
                  'True Heading', 'Speed (knots)']
        if self.stnclass == 'A':
            moreheaders = ['Navigation Status', 'Turn Rate',
                           'Special Maneuver', 'Destination', 'ETA']
            header.extend(moreheaders)
        if self.stntype == 'SAR Aircraft':
            header[4] = 'Altitude (m)'
            header[5] = 'Ground Speed (knots)'
        positionlines.append(stndata)
        positionlines.append(header)
        for posrep in self.posrep:
            posrepline = []
            for item in header:
                try:
                    posrepline.append(posrep[item])
                except KeyError:
                    posrepline.append('')
            positionlines.append(posrepline)
        export.write_csv_file(positionlines, outputfile, dialect=dialect)

    def create_kml_map(self, outputfile, kmzoutput=True, region='A'):
        """
        create a KML map of this stations positions

        Args:
            outputfile(str): full path to output to
            kmzoutput(bool): whether to create a kmz with custom icons (True)
                             or a basic kml file (False)
            region(str): IALA region, default is A
        """
        greenarrows = set()
        orangearrows = set()
        if kmzoutput:
            docpath = os.path.join(os.path.dirname(outputfile), 'doc.kml')
        else:
            docpath = os.path.join(outputfile)
        kmlmap = kml.KMLOutputParser(docpath)
        kmlmap.create_kml_header(
            kmz=kmzoutput, iconsused=self.stntype, ialaregion=region)
        stninfo = self.get_station_info(messagetally=False)
        if self.name != '':
            displayname = self.mmsi + ' - ' + self.name
        else:
            displayname = self.mmsi
        kmlmap.open_folder(displayname)
        posnumber = 1
        for pos in self.posrep:
            timematch = TIMEREGEX.search(pos['Time'])
            if timematch:
                posfoldername = str(posnumber) + ' - ' + timematch.group()
                try:
                    kmltimestamp = kml.convert_timestamp_to_kmltimestamp(
                        pos['Time'])
                except kml.InvalidDateTimeString:
                    kmltimestamp = ''
            else:
                posfoldername = str(posnumber)
                kmltimestamp = ''
            kmlmap.open_folder(posfoldername)
            stninfo['Last Known Position'] = pos
            desc = kmlmap.format_kml_placemark_description(stninfo)
            try:
                alt = str(pos['Altitude (m)'])
            except KeyError:
                alt = '0'
            try:
                heading = pos['True Heading']
                if heading != HEADINGUNAVAILABLE and kmzoutput:
                    greenarrows.add(heading)
                    hdesc = 'TRUE HEADING - {}'.format(heading)
                    kmlmap.add_kml_placemark('TH', hdesc,
                                             str(pos['Longitude']),
                                             str(pos['Latitude']),
                                             str(heading) + 'TH',
                                             alt, kmzoutput, kmltimestamp)
            except KeyError:
                pass
            try:
                cog = int(pos['CoG'])
                if cog != COGUNAVAILABLE and kmzoutput:
                    orangearrows.add(cog)
                    hdesc = 'COURSE OVER GROUND - {}'.format(cog)
                    kmlmap.add_kml_placemark('CoG', hdesc,
                                             str(pos['Longitude']),
                                             str(pos['Latitude']),
                                             str(cog) + 'CoG',
                                             alt, kmzoutput, kmltimestamp)
            except KeyError:
                pass
            try:
                kmlmap.add_kml_placemark(displayname, desc,
                                         str(pos['Longitude']),
                                         str(pos['Latitude']),
                                         self.stntype, alt, kmzoutput,
                                         kmltimestamp)
            except KeyError:
                pass
            kmlmap.close_folder()
            posnumber += 1
        kmlmap.add_kml_placemark_linestring(self.mmsi, self.posrep)
        kmlmap.close_folder()
        kmlmap.close_kml_file()
        kmlmap.write_kml_doc_file()
        if kmzoutput:
            stntypes = [icons.ICONS[self.stntype]]
            kml.make_kmz(outputfile, stntypes, greenarrows, orangearrows)

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
        timingsource(list): the mmsis of AIS base stations used to provide
                           message timings, type 4 messages from this will be
                           used as a timestamp reference
    """

    def __init__(self):
        self.stations = {}
        self.messages = collections.Counter()
        self.messagesprocessed = 0
        self.timings = []
        self.timingsource = []

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
            timestamp(str): time this message was recieved, if provided this
                            will take precedence over timings received from AIS
                            base stations

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
            if timestamp not in self.timings:
                self.timings.append(timestamp)
        else:
            if msgtype in (4, 11) and msgobj.mmsi in self.timingsource:
                if (msgobj.timestamp != TIMEUNAVAILABLE and
                        msgobj.timestamp not in self.timings and
                        kml.DATETIMEREGEX.match(msgobj.timestamp)):
                    self.timings.append(msgobj.timestamp + ' (estimated)')
            try:
                timestamp = self.timings[len(self.timings) - 1]
            except IndexError:
                timestamp = 'N/A'
        msgobj.rxtime = timestamp
        self.stations[msgobj.mmsi].find_position_information(msgobj)
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
        for stn in self.stations_generator():
            try:
                lastpos = stn.get_latest_position()
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
        mmsilist = list(self.stations.keys())
        for stn in mmsilist:
            yield self.stations[stn]

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
        for stn in self.stations_generator():
            stnclasscount[stn.stnclass] += 1
            stntypescount[stn.stntype] += 1
            flagcount[stn.flag] += 1
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
            stats['Times']['Base Station Timing Reference MMSIs'] = \
                self.timingsource
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
        for stn in self.stations_generator():
            allstations[stn.mmsi] = stn.get_station_info(
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
        for stn in self.stations_generator():
            stnclasses[stn.stnclass].append(stn.mmsi)
            stntypes[stn.stntype].append(stn.mmsi)
            flags[stn.flag].append(stn.mmsi)
        organised['Flags'] = flags
        organised['Class'] = stnclasses
        organised['Types'] = stntypes
        return organised

    def create_kml_map(
            self, outputfile, kmzoutput=True, linestring=True, livemap=False,
            livemaptimeout=480, orderby='Types', region='A'):
        """
        create a KML map of all the vessels we have on record

        Args:
            outputfile(str): full path to output to
            kmzoutput(bool): whether to create a kmz with custom icons (True)
                             or a basic kml file (False)
            linestring(bool): display a line showing where the vessel has been
            livemap(bool): is this for a constantly updating KML file
            livemaptimeout(int): if the last postion time of a station is
                                 greater than this, then the station will not
                                 be displayed on the map,
                                 default is 480 seconds (8 minutes)
                                 APPLIES TO LIVE MAP ONLY
            orderby(str): order the stations by 'Types', 'Flags' or 'Class'
                          default is 'Types'
            region(str): IALA region, default is A
        """
        if kmzoutput and not livemap:
            docpath = os.path.join(os.path.dirname(outputfile), 'doc.kml')
        else:
            docpath = os.path.join(outputfile)
        kmlmap = kml.KMLOutputParser(docpath)
        kmlmap.create_kml_header(kmz=kmzoutput, ialaregion=region)
        organisedstns = self.sort_mmsi_by_catagory()
        for catagory in organisedstns[orderby]:
            kmlmap.open_folder(catagory)
            for mmsi in organisedstns[orderby][catagory]:
                stn = self.stations[mmsi]
                try:
                    lastpos = stn.get_latest_position()
                    if livemap:
                        currenttime = datetime.datetime.utcnow()
                        lastpostime = datetime.datetime.strptime(
                            lastpos['Time'], '%Y/%m/%d %H:%M:%S')
                        timediff = currenttime - lastpostime
                        if timediff.seconds > livemaptimeout:
                            continue
                except NoSuitablePositionReport:
                    continue
                stntype = stn.stntype
                stninfo = stn.get_station_info()
                desc = kmlmap.format_kml_placemark_description(stninfo)
                if stn.name != '':
                    displayname = stn.mmsi + ' - ' + stn.name
                else:
                    displayname = stn.mmsi
                kmlmap.open_folder(displayname)
                try:
                    alt = str(lastpos['Altitude (m)'])
                except KeyError:
                    alt = '0'
                try:
                    heading = lastpos['True Heading']
                    if heading != HEADINGUNAVAILABLE and kmzoutput:
                        hdesc = 'TRUE HEADING - {}'.format(heading)
                        kmlmap.add_kml_placemark(
                            'TH', hdesc,
                            str(lastpos['Longitude']),
                            str(lastpos['Latitude']),
                            str(heading) + 'TH', alt, kmzoutput)
                except KeyError:
                    pass
                try:
                    cog = int(lastpos['CoG'])
                    if cog != COGUNAVAILABLE and kmzoutput:
                        hdesc = 'COURSE OVER GROUND - {}'.format(cog)
                        kmlmap.add_kml_placemark('CoG', hdesc,
                                                 str(lastpos['Longitude']),
                                                 str(lastpos['Latitude']),
                                                 str(cog) + 'CoG',
                                                 alt, kmzoutput)
                except KeyError:
                    pass
                if linestring:
                    posreps = stn.posrep
                    kmlmap.add_kml_placemark_linestring(stn.mmsi, posreps)
                kmlmap.add_kml_placemark(displayname, desc,
                                         str(lastpos['Longitude']),
                                         str(lastpos['Latitude']),
                                         stntype, alt, kmzoutput)
                kmlmap.close_folder()
            kmlmap.close_folder()
        kmlmap.close_kml_file()
        kmlmap.write_kml_doc_file()
        if kmzoutput and not livemap:
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
        for stn in self.stations_generator():
            try:
                lastpos = stn.get_latest_position()
            except NoSuitablePositionReport:
                continue
            currentmmsi = stn.mmsi
            currentproperties = {}
            currentproperties.update(
                stn.get_station_info())
            currentproperties['Icon'] = \
                icons.ICONS[stn.stntype]
            try:
                currentproperties['Heading'] = lastpos['True Heading']
            except KeyError:
                currentproperties['Heading'] = HEADINGUNAVAILABLE
            lastlat = lastpos['Latitude']
            lastlon = lastpos['Longitude']
            currentcoords = []
            for pos in stn.posrep:
                currentcoords.append([pos['Longitude'], pos['Latitude']])
            geojsonmap.add_station_info(currentmmsi,
                                        currentproperties,
                                        currentcoords,
                                        lastlon,
                                        lastlat)
        if outputfile:
            geojsonmap.save_to_file(outputfile)
        return geojsonmap

    def create_nav_table(self, mmsilist=None):
        """
        creates a table of data we have on all vessels

        Note:
            this is a list of lists meant for output to a live updating GUI

        Args:
            mmsilist(list): list of MMSIs as strings if this is specified
                            we will only display info on these MMSIs

        Returns:
            csvtable(list): (lists of lists) each list is a line
                            in the table
        """
        csvtable = []
        lastposheader = ['Latitude', 'Longitude', 'CoG', 'Speed (knots)',
                         'Navigation Status', 'Turn Rate', 'Time']
        if mmsilist:
            stations = mmsilist
        else:
            stations = self.stations_generator()
        for stn in stations:
            stninfo = stn.get_station_info()
            line = []
            for item in lastposheader:
                try:
                    stninfo[item] = (stninfo['Last Known Position'][item])
                except (NoSuitablePositionReport, TypeError, KeyError):
                    stninfo[item] = ''
            for item in NAVHEADERS:
                try:
                    line.append(stninfo[item])
                except KeyError:
                    line.append('')
            csvtable.append(line)
        return csvtable

    def create_table_data(self, mmsilist=None, csvheader=None,
                          posheaders=None):
        """
        creates a table of data we have on all vessels

        Note:
            this is a list of lists meant for output to a csv file
            use the function export.write_csv_file to do this

        Args:
            mmsilist(list): list of MMSIs as strings if this is specified
                            we will only display info on these MMSIs
            csvheader(list): specify the header fields to be displayed for
                             the outputted table, this is for custom tables,
                             if in doubt leave this as None for default headers
            posheaders(list): headers that appear in the station position
                              reports this is for custom tables, if in doubt
                              leave this as None for default headers

        Returns:
            csvtable(list): (lists of lists) each list is a line
                            in the csv file
        """
        csvtable = []
        if not csvheader:
            csvheader = [
                'MMSI', 'Class', 'Type', 'Flag', 'Name', 'Callsign',
                'IMO number', 'RAIM in use', 'EPFD Fix type',
                'Position Accuracy', 'Total Messages',
                'First Known Latitude',
                'First Known Longitude', 'First Known Navigation Status',
                'First Known Time', 'Last Known Latitude',
                'Last Known Longitude', 'Last Known Navigation Status',
                'Last Known Time', 'Destination', 'ETA']
        if not posheaders:
            posheaders = ['Latitude', 'Longitude', 'Navigation Status', 'Time']
        csvtable.append(csvheader)
        if mmsilist:
            stations = mmsilist
        else:
            stations = self.stations_generator()
        for stn in stations:
            stninfo = stn.get_station_info()
            line = []
            stninfo['Total Messages'] = 0
            for i in stn.sentmsgs:
                stninfo['Total Messages'] += stn.sentmsgs[i]
            try:
                firstpos = stn.posrep[0]
            except IndexError:
                firstpos = {}
            for item in posheaders:
                try:
                    stninfo['First Known ' + item] = (firstpos[item])
                except (NoSuitablePositionReport, TypeError, KeyError):
                    stninfo['First Known ' + item] = ''
            for item in posheaders:
                try:
                    stninfo['Last Known ' + item] = \
                        (stninfo['Last Known Position'][item])
                except (NoSuitablePositionReport, TypeError, KeyError):
                    stninfo['Last Known ' + item] = ''
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


class BaseStationTracker(AISTracker):
    """
    class to process AIS Base Stations to use for timing data
    """

    def process_message(self, data):
        """
        determine what type of AIS message it is

        Args:
            data(str): full message payload from 1 or more NMEA sentences

        Raises:
            InvalidMMSI: if the mmsi = 000000000

        Returns:
            msgobj(messages.aismessage.AISMessage): the ais message type object
        """
        msgbinary = binary.ais_sentence_payload_binary(data)
        msgtype = binary.decode_sixbit_integer(msgbinary[0:6])
        if msgtype in (4, 11):
            msgobj = allmessages.MSGTYPES[msgtype](msgbinary)
            if msgobj.mmsi == '000000000':
                raise InvalidMMSI('Invalid MMSI - 000000000')
            if msgobj.mmsi not in self.stations:
                self.stations[msgobj.mmsi] = AISStation(msgobj.mmsi)
            if self.stations[msgobj.mmsi].stnclass == 'Unknown':
                self.stations[msgobj.mmsi].determine_station_class(msgobj)
            msgobj.rxtime = msgobj.timestamp
            self.stations[msgobj.mmsi].find_position_information(msgobj)
            self.messagesprocessed += 1
            self.messages[allmessages.MSGDESCRIPTIONS[msgtype]] += 1

    def __str__(self):
        strtext = ('AIS Base Station Tracker - tracking {} Base Stations'
                   ' , processed {} messages,').format(
                       str(self.__len__()),
                       str(self.messagesprocessed))
        return strtext


class UnknownMessageType(Exception):
    """
    raise when an unknown AIS message type is encountered
    """


class InvalidMMSI(Exception):
    """
    raise when an incorrect MMSI is encountered
    """


class NoSuitablePositionReport(Exception):
    """
    raise if we cannot get a position
    """
