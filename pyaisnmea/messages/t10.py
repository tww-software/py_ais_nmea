"""
Type 10 messages are used by stations to request a UTC timestamp from an AIS
base staion.
"""

import pyaisnmea.messages.aismessage


class Type10UTCDateInquiry(pyaisnmea.messages.aismessage.AISMessage):
    """
    Used by stations to request UTC time from an AIS base station
    base station should respond with a Type 11 reply
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.destinationmmsi = self.decode_sixbit_integer(msgbinary[40:70])

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = '{} to {} from {}'.format(self.description,
                                            self.destinationmmsi, self.mmsi)
        return strtext
