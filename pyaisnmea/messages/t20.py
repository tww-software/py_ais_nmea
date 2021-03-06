"""
Type 20 messages are used to pre-allocate TDMA slots within an AIS base
station network.
"""

import pyaisnmea.messages.aismessage


class Type20DatalinkManagementMessage(
        pyaisnmea.messages.aismessage.AISMessage):
    """
    Type 20 Datalink Management Message

    Used to pre allocate TDMA slots in a AIS Base Station network.
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.offsetno1 = self.decode_sixbit_integer(msgbinary[40:52])
        self.reservedslots1 = self.decode_sixbit_integer(msgbinary[52:56])
        self.timeout1 = self.decode_sixbit_integer(msgbinary[56:59])
        self.increment1 = self.decode_sixbit_integer(msgbinary[59:70])
        self.offsetno2 = self.decode_sixbit_integer(msgbinary[70:82])
        self.reservedslots2 = self.decode_sixbit_integer(msgbinary[82:86])
        self.timeout2 = self.decode_sixbit_integer(msgbinary[86:89])
        self.increment2 = self.decode_sixbit_integer(msgbinary[89:100])
        self.offsetno3 = self.decode_sixbit_integer(msgbinary[100:112])
        self.reservedslots3 = self.decode_sixbit_integer(msgbinary[112:116])
        self.timeout3 = self.decode_sixbit_integer(msgbinary[116:119])
        self.increment3 = self.decode_sixbit_integer(msgbinary[119:130])
        self.offsetno4 = self.decode_sixbit_integer(msgbinary[130:142])
        self.reservedslots4 = self.decode_sixbit_integer(msgbinary[142:146])
        self.timeout4 = self.decode_sixbit_integer(msgbinary[146:149])
        self.increment4 = self.decode_sixbit_integer(msgbinary[149:160])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}').format(self.description, self.mmsi)
        return strtext
