import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type9StandardSARAircraftPositionReport(
    pyaisnmea.messages.aismessage.AISMessage):
    """
    SAR aircraft position report

    Attributes:
        alitude(int): altitude in metres
        speedoverground(int): speed tracking over the ground in knots
        posfixaccuracy(bool): 1 = accuracy < 10m, 0 = accuracy > 10m
        longitude(float): longitude in decimal degrees, 181 means not available
        latitude(float): latitude in decimal degrees, 91 means not available
        courseoverground(float): direction the ship is moving,
                               3600 if not available
        timestampsecond(int): second of the UTC time stamp when
                              the message was sent
        dte(str): data terminal equipment status
        raim(bool): is Receiver Autonomous Integrity Monitoring in use?
                       raim checks the GPS position is accurate
                       1 = True 0 = False
        radiostatus(int): radio diagnostic info
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.altitude = self.decode_sixbit_integer(msgbinary[38:50])
        self.speedoverground = self.decode_sixbit_integer(msgbinary[50:60])
        self.posfixaccuracy = self.accuracy[self.decode_sixbit_integer(
            msgbinary[60:61])]
        self.longitude = binary.decode_twos_complement(
            msgbinary[61:89]) / 600000.0
        self.latitude = binary.decode_twos_complement(
            msgbinary[89:116]) / 600000.0
        self.courseoverground = self.decode_sixbit_integer(
            msgbinary[116:128]) / 10
        self.timestampsecond = self.decode_sixbit_integer(
            msgbinary[128:134])
        self.dte = self.dtevalues[self.decode_sixbit_integer(
            msgbinary[142:143])]
        self.raim = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[147:148])]
        self.radiostatus = self.decode_sixbit_integer(msgbinary[148:168])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, Altitude(m): {}, '
                   'Ground Speed(knots): {},'
                   'Location: {},{}').format(self.description, self.mmsi,
                                             self.altitude,
                                             self.speedoverground,
                                             self.latitude,
                                             self.longitude)
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
        details['DTE'] = self.dte
        return details

    def get_position_data(self):
        """
        get the position data from this message

        Returns:
            posrep(dict): position and navigation details from the message
        """
        posrep = {
            'Altitude (m)': self.altitude,
            'CoG': self.courseoverground,
            'Ground Speed (knots)': self.speedoverground,
            'Latitude': self.latitude,
            'Longitude': self.longitude}
        return posrep
