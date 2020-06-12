"""
Type 18 messages are postion reports sent by Class B AIS stations.
"""

import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type18PositionReportClassB(pyaisnmea.messages.aismessage.AISMessage):
    """
    position report for Class B equipment

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
        csunit(str): 0 = SOTDMA unit, 1 = Carrier Sense unit
        displayflag(bool): 0 = unit has no display, 1 = unit has display
        dscflag(bool): 1 means the unit is connected to a VHF radio with
                      DSC capability
        bandflag(bool): if 1 then base stations can order this unit
                       to switch frequency
        message22flag(bool): if 1 then then unit can accept channel assignment
                            from type 22 messages
        assignedmodeflag(str): 0 = autonomous mode, 1 = assigned mode
        raim(bool): is Receiver Autonomous Integrity Monitoring in use?
                       raim checks the GPS position is accurate
                       1 = True 0 = False
        radiostatus(int): radio diagnostic info
    """

    csdict = {0: 'Class B SOTDMA unit', 1: 'Class B CS (Carrier Sense) unit'}
    assignmentmode = {0: 'Autonomous Mode', 1: 'Assigned Mode'}

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
        self.csunit = self.csdict[self.decode_sixbit_integer(
            msgbinary[141:142])]
        self.displayunit = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[142:143])]
        self.dscflag = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[143:144])]
        self.bandflag = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[144:145])]
        self.message22flag = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[145:146])]
        self.assignedmodeflag = self.assignmentmode[
            self.decode_sixbit_integer(msgbinary[146:147])]
        self.raim = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[147:148])]
        self.radiostatus = self.decode_sixbit_integer(msgbinary[148:168])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, Timestamp seconds: {},'
                   ' Location: {},{}, Speed: {}, '
                   'True Heading: {}').format(self.description, self.mmsi,
                                              self.timestampsecond,
                                              self.latitude, self.longitude,
                                              self.speed, self.trueheading)
        return strtext

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        details = {}
        details['RAIM in use'] = self.raim
        details['Position Accuracy'] = self.posfixaccuracy
        details['Has Display'] = self.displayunit
        details['DSC enabled'] = self.dscflag
        details['Use Other Frequencies'] = self.bandflag
        details['Accept Channel Assignment From Type 22 Messages'] = \
            self.message22flag
        details['Assignment Mode'] = self.assignedmodeflag
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
