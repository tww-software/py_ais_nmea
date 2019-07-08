import binary

import messages.aismessage


class Type17DGNSSBroadcastBinaryMessage(messages.aismessage.AISMessage):
    """
    used to broadcast differential corrections for GPS
    """

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - source MMSI: {}'
                   '').format(self.description, self.mmsi)
        return strtext
