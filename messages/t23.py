import binary

import messages.aismessage


class Type23GroupAssignmentCommand(messages.aismessage.AISMessage):
    """
    NO REAL LIFE TEST DATA FOUND YET!
    """

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('Group Assignment Command - source MMSI: {}'
                   '').format(self.mmsi)
        return strtext
