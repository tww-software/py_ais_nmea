import binary

import messages.aismessage


class Type123PositionReportClassA(messages.aismessage.AISMessage):
    """
    used by AIS class A transponders to send position information

    Attributes:
        navstatus(str): current navigation status - what the ship is doing
        turnrate(int): how fast the ship is turning
                       0 is not turning
                       128 = turn rate not available
        speed(float): speed in knots, 1023 = not available
        posfixaccuracy(bool): 1 = accuracy < 10m, 0 = accuracy > 10m
        longitude(float): longitude in decimal degrees, 181 = not available
        latitude(float): latitude in decimal degrees, 91 = not available
        courseoverground(float): direction the ship is moving,
                               3600 if not available
        trueheading(int): direction the ships bow is pointed,
                          511 = not available
        timestampsecond(int): second of the UTC time stamp
                              when the message was sent
        maneuverindicator(str): is the ship persorming a special maneuver
        raim(bool): is Receiver Autonomous Integrity Monitoring in use?
                       raim checks the GPS position is accurate
                       1 = True 0 = False
        radiostatus(int): radio diagnostic info
    """
    maneuvers = {0: 'not available/default', 1: 'no special maneuver',
                 2: 'special maneuver'}

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.navstatus = self.navstatustypes[self.decode_sixbit_integer(
            msgbinary[38:42])]
        self.turnrate = self.decode_sixbit_integer(msgbinary[42:50])
        self.speed = self.decode_sixbit_integer(msgbinary[50:60]) / 10
        self.posfixaccuracy = self.accuracy[self.decode_sixbit_integer(
            msgbinary[60:61])]
        self.longitude = binary.decode_twos_complement(
            msgbinary[61:89]) / 600000.0
        self.latitude = binary.decode_twos_complement(
            msgbinary[89:116]) / 600000.0
        self.courseoverground = self.decode_sixbit_integer(
            msgbinary[116:128]) / 10
        self.trueheading = self.decode_sixbit_integer(msgbinary[128:137])
        self.timestampsecond = self.decode_sixbit_integer(
            msgbinary[137:143])
        self.maneuverindicator = self.manuvers[self.decode_sixbit_integer(
            msgbinary[143:145])]
        self.raim = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[148:149])]
        self.radiostatus = self.decode_sixbit_integer(msgbinary[149:168])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, '
                   ' Location: {},{}, Speed: {}, True Heading: {}, CoG: {}, '
                   'Navigation Status: {}').format(self.description,
                                                   self.mmsi,
                                                   self.latitude,
                                                   self.longitude,
                                                   self.speed,
                                                   self.trueheading,
                                                   self.courseoverground,
                                                   self.navstatus)
        return strtext

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        details = {}
        details['Position Accuracy'] = self.posfixaccuracy
        details['RAIM in use'] = self.raim
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
            'Navigation Status': self.navstatus,
            'Turn Rate': self.turnrate,
            'Special Maneuver': self.maneuverindicator,
            'Latitude': self.latitude,
            'Longitude': self.longitude}
        return posrep
