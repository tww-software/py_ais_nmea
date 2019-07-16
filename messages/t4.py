import binary

import messages.aismessage


class Type4BaseStationReport(messages.aismessage.AISMessage):
    """
    Report sent by coastal AIS Base Stations

    Note:
        EPFD = electronic position fixing device

    Attributes:
        timestamp(str): the timestamp in UTC "%Y %m %D - %H:%M:%S"
        posfixaccuracy(bool): 1 = accuracy < 10m, 0 = accuracy > 10m
        longitude(float): longitude in decimal degrees, 181 means not available
        latitude(float): latitude in decimal degrees, 91 means not available
        epfdfixtype(str): how the EPFD aquires its position fix
        raim(bool): is Receiver Autonomous Integrity Monitoring in use?
                       raim checks the GPS position is accurate
                       1 = True 0 = False
        sotdmastate(int): Self-organized time-division multiple access
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        year = self.decode_sixbit_integer(msgbinary[38:52])
        month = self.decode_sixbit_integer(msgbinary[52:56])
        day = self.decode_sixbit_integer(msgbinary[56:61])
        hour = self.decode_sixbit_integer(msgbinary[61:66])
        minute = self.decode_sixbit_integer(msgbinary[66:72])
        second = self.decode_sixbit_integer(msgbinary[72:78])
        self.timestamp = '{}{:02d}{:02d}_{:02d}{:02d}{:02d}'.format(
            year, month, day, hour, minute, second)
        self.posfixaccuracy = self.accuracy[self.decode_sixbit_integer(
            msgbinary[78:79])]
        self.longitude = binary.decode_twos_complement(
            msgbinary[79:107]) / 600000.0
        self.latitude = binary.decode_twos_complement(
            msgbinary[107:134]) / 600000.0
        self.epfdfixtype = self.epfdfixtypes[self.decode_sixbit_integer(
            msgbinary[134:138])]
        self.raim = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[148:149])]
        self.sotdmastate = self.decode_sixbit_integer(msgbinary[149:168])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, Timestamp: {}, '
                   'Location: {},{}').format(self.description, self.mmsi,
                                             self.timestamp,
                                             self.latitude, self.longitude)
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
        details['Last Timestamp'] = self.timestamp
        details['EPFD Fix type'] = self.epfdfixtype
        details['SOTDMA State'] = self.sotdmastate
        return details

    def get_position_data(self):
        """
        get the position data from this message

        Returns:
            posrep(dict): position and navigation details from the message
        """
        posrep = {
            'Time Stamp (UTC)': self.timestamp,
            'Latitude': self.latitude,
            'Longitude': self.longitude}
        return posrep
