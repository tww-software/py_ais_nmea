import binary

import messages.aismessage


class Type22ChannelManagement(messages.aismessage.AISMessage):
    """
    NO REAL LIFE TEST DATA FOUND YET!
    """
    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.channela = self.decode_sixbit_integer(msgbinary[40:52])
        self.channelb = self.decode_sixbit_integer(msgbinary[52:64])
        self.txrxmode = self.decode_sixbit_integer(msgbinary[64:68])
        self.highpower = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[68:69])]

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - source MMSI: {}'
                   '').format(self.description, self.mmsi)
        return strtext
