import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type27LongRangeAISPositionReport(
    pyaisnmea.messages.aismessage.AISMessage):
    """
    used by class A eqipment for long range detection (ussualy by satellite)

    Attributes:
        posfixaccuracy(bool): 1 = accuracy < 10m, 0 = accuracy > 10m
        raim(bool): is Receiver Autonomous Integrity Monitoring in use?
                       raim checks the GPS position is accurate
                       1 = True 0 = False
        navstatus(str): current navigation status - what the ship is doing
        longitude(float): longitude in decimal degrees, 181 means not available
        latitude(float): latitude in decimal degrees, 91 means not available
        speed(float): speed in knots
        courseoverground(int): direction the ship is moving,
                               3600 if not available
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.posfixaccuracy = self.accuracy[self.decode_sixbit_integer(
            msgbinary[38:39])]
        self.raim = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[39:40])]
        self.navstatus = self.navstatustypes[self.decode_sixbit_integer(
            msgbinary[40:44])]
        self.longitude = binary.decode_twos_complement(
            msgbinary[44:62]) / 600.0
        self.latitude = binary.decode_twos_complement(msgbinary[62:79]) / 600.0
        self.speed = self.decode_sixbit_integer(msgbinary[79:85]) / 10
        self.courseoverground = self.decode_sixbit_integer(msgbinary[85:94])
        self.gnsspositon = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[94:95])]

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, Location:'
                   ' {},{}').format(self.description, self.mmsi,
                                    self.latitude, self.longitude)
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
        return details

    def get_position_data(self):
        """
        get the position data from this message

        Returns:
            posrep(dict): position and navigation details from the message
        """
        posrep = {
            'Navigation Status': self.navstatus,
            'Speed (knots)': self.speed,
            'CoG': self.courseoverground,
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'Time': self.rxtime}
        return posrep
