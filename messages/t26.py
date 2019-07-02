import binary

import messages.aismessage


class Type26MultipleSlotBinaryMessage(messages.aismessage.AISMessage):
    """
    NO REAL LIFE TEST DATA FOUND YET!
    """

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('Multiple Slot Binary Message - source MMSI: {}'
                   '').format(self.mmsi)
        return strtext
