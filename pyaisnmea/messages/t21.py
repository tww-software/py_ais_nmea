import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type21AidToNavigation(pyaisnmea.messages.aismessage.AISMessage):
    """
    Type 21 message for Aids to Navigation

    sent out by navigations aids such as buoys and lighthouses to report their
    position

    Attributes:
        aidtype(str) the type of aid (found in navaidtypes dict)
        name(str) the name of the navigation aid
        posfixaccuracy(str): 1 = accuracy < 10m, 0 = accuracy > 10m
        longitude(float): longitude in decimal degrees, 181 means not available
        latitude(float): latitude in decimal degrees, 91 means not available
        length(int): ship length in metres
        width(int): ship width in metres
        epfdfixtype(str): how the EPFD aquires its position fix
        timestampsecond(int): second of the UTC time stamp when the
                              message was sent
        offposition(bool): is the nav aid off position (for floating nav aids)
        raim(bool): is Receiver Autonomous Integrity Monitoring in use?
                        raim checks the GPS position is accurate
                        1 = True 0 = False
        virtualaid(bool): is this a virtual nav aid transmitted by a nearby
                          AIS base station
        assignedmode(bool): is the nav aid operating in assigned mode
    """

    navaidtypes = {0: 'Default Nav Aid, not specified',
                   1: 'Reference point',
                   2: 'RACON (radar transponder marking a navigation hazard)',
                   3: 'Fixed structure off shore, such as oil platforms,'
                      ' wind farms,',
                   4: 'Spare, Reserved for future use.',
                   5: 'Light, without sectors',
                   6: 'Light, with sectors',
                   7: 'Leading Light Front',
                   8: 'Leading Light Rear',
                   9: 'Beacon, Cardinal N',
                   10: 'Beacon, Cardinal E',
                   11: 'Beacon, Cardinal S',
                   12: 'Beacon, Cardinal W',
                   13: 'Beacon, Port hand',
                   14: 'Beacon, Starboard hand',
                   15: 'Beacon, Preferred Channel port hand',
                   16: 'Beacon, Preferred Channel starboard hand',
                   17: 'Beacon, Isolated danger',
                   18: 'Beacon, Safe water',
                   19: 'Beacon, Special mark',
                   20: 'Cardinal Mark N',
                   21: 'Cardinal Mark E',
                   22: 'Cardinal Mark S',
                   23: 'Cardinal Mark W',
                   24: 'Port hand Mark',
                   25: 'Starboard hand Mark',
                   26: 'Preferred Channel Port hand',
                   27: 'Preferred Channel Starboard hand',
                   28: 'Isolated danger',
                   29: 'Safe Water',
                   30: 'Special Mark',
                   31: 'Light Vessel / LANBY / Rigs'}

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.aidtype = self.navaidtypes[self.decode_sixbit_integer(
            msgbinary[38:43])]
        name = binary.decode_sixbit_ascii(msgbinary[43:163]).rstrip()
        self.posfixaccuracy = self.accuracy[self.decode_sixbit_integer(
            msgbinary[163:164])]
        self.longitude = binary.decode_twos_complement(
            msgbinary[164:192]) / 600000.0
        self.latitude = binary.decode_twos_complement(
            msgbinary[192:219]) / 600000.0
        tobow = self.decode_sixbit_integer(msgbinary[219:228])
        tostern = self.decode_sixbit_integer(msgbinary[228:237])
        toport = self.decode_sixbit_integer(msgbinary[237:243])
        tostarboard = self.decode_sixbit_integer(msgbinary[243:249])
        self.length = tobow + tostern
        self.width = toport + tostarboard
        self.epfdfixtype = self.epfdfixtypes[self.decode_sixbit_integer(
            msgbinary[249:253])]
        self.timestampsecond = self.decode_sixbit_integer(
            msgbinary[253:259])
        self.offposition = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[259:260])]
        self.raim = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[268:269])]
        self.virtualaid = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[269:270])]
        self.assignedmode = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[270:271])]
        nameextension = binary.decode_sixbit_ascii(
            msgbinary[272:361]).rstrip()
        self.name = name + nameextension

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, Name: {}, Type: {}, '
                   'Location: {},{}').format(self.description, self.mmsi,
                                             self.name,
                                             self.aidtype, self.latitude,
                                             self.longitude)
        return strtext

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        details = {}
        details['Width (m)'] = self.width
        details['Length (m)'] = self.length
        details['Navigation Aid Type'] = self.aidtype
        details['EPFD Fix type'] = self.epfdfixtype
        details['RAIM in use'] = self.raim
        details['Virtual Navigation Aid'] = self.virtualaid
        details['Position Accuracy'] = self.posfixaccuracy
        details['Off Position'] = self.offposition
        details['Assigned Mode'] = self.assignedmode
        return details

    def get_position_data(self):
        """
        get the position data from this message

        Returns:
            posrep(dict): position and navigation details from the message
        """
        posrep = {
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'Time': self.rxtime}
        return posrep

