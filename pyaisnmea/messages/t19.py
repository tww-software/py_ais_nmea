import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type19ExtendedReportClassB(pyaisnmea.messages.aismessage.AISMessage):
    """
    Extended Class B Position Report - more information than a type 18 message

    Attributes:
        speed(float): speed in knots
        posfixaccuracy(bool): 1 = accuracy < 10m, 0 = accuracy > 10m
        longitude(float): longitude in decimal degrees, 181 means not available
        latitude(float): latitude in decimal degrees, 91 means not available
        courseoverground(float): direction the ship is moving,
                               3600 if not available
        trueheading(int): direction the ships bow is pointed
        timestampsecond(int): second of the UTC time stamp when the
                              message was sent
        name(str): the name of the vessel
        shiptype(str): the type of ship - lookup from self.shiptypes
        length(int): ship length in metres
        width(int): ship width in metres
        epfdfixtype(str): how the EPFD aquires its position fix
        raim(bool): is Receiver Autonomous Integrity Monitoring in use?
                    raim checks the GPS position is accurate
        dte(str): is device operating as Data Terminal Equipment
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.speed = self.decode_sixbit_integer(msgbinary[46:56]) / 10
        self.posfixaccuracy = self.accuracy[self.decode_sixbit_integer(
            msgbinary[46:47])]
        self.longitude = binary.decode_twos_complement(
            msgbinary[57:85]) / 600000.0
        self.latitude = binary.decode_twos_complement(
            msgbinary[85:112]) / 600000.0
        self.courseoverground = self.decode_sixbit_integer(
            msgbinary[112:124]) / 10
        self.trueheading = self.decode_sixbit_integer(msgbinary[124:133])
        self.timestampsecond = self.decode_sixbit_integer(
            msgbinary[133:139])
        self.name = binary.decode_sixbit_ascii(msgbinary[143:263]).rstrip()
        try:
            self.shiptype = self.shiptypes[self.decode_sixbit_integer(
                msgbinary[263:271])]
        except KeyError:
            self.shiptype = 'Unknown'
        tobow = self.decode_sixbit_integer(msgbinary[271:280])
        tostern = self.decode_sixbit_integer(msgbinary[280:289])
        toport = self.decode_sixbit_integer(msgbinary[289:295])
        tostarboard = self.decode_sixbit_integer(msgbinary[295:301])
        self.length = tobow + tostern
        self.width = toport + tostarboard
        self.epfdfixtype = self.epfdfixtypes[self.decode_sixbit_integer(
            msgbinary[301:305])]
        self.raim = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[305:306])]
        self.dte = self.dtevalues[self.decode_sixbit_integer(
            msgbinary[306:307])]

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, Timestamp seconds: {},'
                   ' Location: {},{}, Speed: {}, True Heading: {}'
                   'Name: {}, Ship Type: {}, Length: {}, Width: {}'
                   '').format(self.description, self.mmsi,
                              self.timestampsecond,
                              self.latitude, self.longitude,
                              self.speed, self.trueheading,
                              self.name, self.shiptype,
                              self.length, self.width)
        return strtext

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        details = {}
        details['EPFD Fix type'] = self.epfdfixtype
        details['Width (m)'] = self.width
        details['Length (m)'] = self.length
        details['RAIM in use'] = self.raim
        details['DTE'] = self.dte
        return details

    def get_position_data(self):
        """
        get the position data from this message

        Returns:
            posrep(dict): position and navigation details from the message
        """
        posrep = {
            'Speed (knots)': self.speed,
            'True Heading': self.trueheading,
            'CoG': self.courseoverground,
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'Time': self.rxtime}
        return posrep
