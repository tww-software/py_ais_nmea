"""
Type 15 messages are used by AIS base stations to interrogate up to 2 MMSIs.
"""

import pyaisnmea.messages.aismessage


class Type15Interrogation(pyaisnmea.messages.aismessage.AISMessage):
    """
    used by AIS base stations to interrogate up to 2 MMSIs

    Attributes:
        self.interrogatedmmsi1(int): first MMSI to interrogate
        self.firstmessagetype(int): message type for first MMSI
        self.firstslotoffset(int):  offset for first message from first MMSI
        self.secondmessagetype(int): second message type for first MMSI
        self.secondslotoffset(int): offset for second message type
                                    for first MMSI
        self.interrogatedmmsi2(int): second MMSI to interrogate
        self.firstmessagetype2(int): message type for second MMSI
        self.firstslotoffset2(int): offset for 1st message type of second MMSI
    """
    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.interrogatedmmsi1 = self.decode_sixbit_integer(
            msgbinary[40:70])
        self.firstmessagetype = self.decode_sixbit_integer(msgbinary[70:76])
        self.firstslotoffset = self.decode_sixbit_integer(msgbinary[76:88])
        self.secondmessagetype = self.decode_sixbit_integer(
            msgbinary[90:96])
        self.secondslotoffset = self.decode_sixbit_integer(
            msgbinary[96:108])
        self.interrogatedmmsi2 = self.decode_sixbit_integer(
            msgbinary[110:140])
        self.firstmessagetype2 = self.decode_sixbit_integer(
            msgbinary[140:146])
        self.firstslotoffset2 = self.decode_sixbit_integer(
            msgbinary[146:158])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = '{} - source MMSI: {}'.format(self.description, self.mmsi)
        return strtext
