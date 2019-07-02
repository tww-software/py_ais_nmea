import binary

import messages.aismessage


class Type15Interrogation(messages.aismessage.AISMessage):
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
        self.interrogatedmmsi1 = binary.decode_sixbit_integer(
            msgbinary, 40, 70)
        self.firstmessagetype = binary.decode_sixbit_integer(msgbinary, 70, 76)
        self.firstslotoffset = binary.decode_sixbit_integer(msgbinary, 76, 88)
        self.secondmessagetype = binary.decode_sixbit_integer(
            msgbinary, 90, 96)
        self.secondslotoffset = binary.decode_sixbit_integer(
            msgbinary, 96, 108)
        self.interrogatedmmsi2 = binary.decode_sixbit_integer(
            msgbinary, 110, 140)
        self.firstmessagetype2 = binary.decode_sixbit_integer(
            msgbinary, 140, 146)
        self.firstslotoffset2 = binary.decode_sixbit_integer(
            msgbinary, 146, 158)

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = 'Interrogation - source MMSI: {}'.format(self.mmsi)
        return strtext
