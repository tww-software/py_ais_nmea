import binary

import messages.aismessage


class Type10UTCDateInquiry(messages.aismessage.AISMessage):
    """
    Used by stations to request UTC time from an AIS base station
    base station should respond with a Type 11 reply
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.destinationmmsi = binary.decode_sixbit_integer(msgbinary, 40, 70)

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = 'UTC Date Inquiry to {} from {}'.format(self.destinationmmsi,
                                                          self.mmsi)
        return strtext
