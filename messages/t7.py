import binary

import messages.aismessage


class Type7BinaryAcknowlegement(messages.aismessage.AISMessage):
    """
    Type 7 Acknowlegement to a Type 6 Binary Message

    Attributes:
        mmsi 1 to 4 (int): acknowlege messages for up to 4 different MMSI's
        senders(list): filtered list of senders to acknowlege
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.mmsi1 = binary.decode_sixbit_integer(msgbinary, 40, 70)
        self.mmsi2 = binary.decode_sixbit_integer(msgbinary, 72, 102)
        self.mmsi3 = binary.decode_sixbit_integer(msgbinary, 104, 134)
        self.mmsi4 = binary.decode_sixbit_integer(msgbinary, 136, 166)
        self.senders = self.filter_senders()

    def filter_senders(self):
        """
        remove any 'unavailable' items from the senders list
        so only actual MMSIs are displayed

        Returns:
            senders2(list): list of sender MMSIs
        """
        senders = [self.mmsi1, self.mmsi2, self.mmsi3, self.mmsi4]
        senders2 = []
        for mmsi in senders:
            if mmsi != 'unavailable':
                senders2.append(str(mmsi))
        return senders2

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} by {} to'
                   ' message from {}').format(self.description, self.mmsi,
                                              ' '.join(self.senders))
        return strtext
