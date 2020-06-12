"""
Type 11 messages are sent in response to a Type 10 message. They are the same
format as a Type 4 message.
"""

import pyaisnmea.messages.aismessage


class Type11UTCDateResponse(pyaisnmea.messages.t4.Type4BaseStationReport):
    """
    appears to be identical to a regular base station report
    """

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - MMSI: {}, Timestamp: {}, '
                   'Location: {},{}').format(self.description, self.mmsi,
                                             self.timestamp,
                                             self.latitude, self.longitude)
        return strtext
