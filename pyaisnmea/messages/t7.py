"""
Type 7 messages are acknowlegements send in response to a Type 6 message.
"""

import pyaisnmea.messages.aismessage


class Type7BinaryAcknowlegement(pyaisnmea.messages.aismessage.AISMessage):
    """
    Type 7 Acknowlegement to a Type 6 Binary Message

    Attributes:
        mmsi 1 to 4 (int): acknowlege messages for up to 4 different MMSI's
        senders(list): filtered list of senders to acknowlege
    """

    fields = {'MMSI 1':{'start': 40, 'end': 70},
              'MMSI 2':{'start': 72, 'end': 102},
              'MMSI 3':{'start': 104, 'end': 134},
              'MMSI 4':{'start': 136, 'end': 166}}

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        senders = []
        for field in self.fields:
            try:
                sentmmsi = self.decode_sixbit_integer(
                    msgbinary[self.fields[field]['start']:self.fields[field]['end']])
                senders.append(sentmmsi)
            except IndexError:
                pass
        self.senders = self.filter_senders(senders)

    @staticmethod
    def filter_senders(senders):
        """
        remove any 'unavailable' items from the senders list
        so only actual MMSIs are displayed

        Returns:
            senders2(list): list of sender MMSIs
        """
        senders2 = []
        for mmsi in senders:
            if mmsi != 0:
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
