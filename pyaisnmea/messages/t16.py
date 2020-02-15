import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type16AssignmentModeCommand(pyaisnmea.messages.aismessage.AISMessage):
    """
    NO REAL LIFE TEST DATA FOUND YET!
    """
    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.destinationammsi = self.decode_sixbit_integer(msgbinary[40:70])
        self.offseta = self.decode_sixbit_integer(msgbinary[70:82])
        self.incrementa = self.decode_sixbit_integer(msgbinary[82:92])
        self.destinationbmmsi = self.decode_sixbit_integer(
            msgbinary[92:122])
        self.offsetb = self.decode_sixbit_integer(msgbinary[122:134])
        self.incrementb = self.decode_sixbit_integer(msgbinary[134:144])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = '{} - source MMSI: {}'.format(self.description, self.mmsi)
        return strtext
