import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type14SafetyBroadcastMessage(pyaisnmea.messages.aismessage.AISMessage):
    """
    Safety Broadcast Message
    """
    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.msgtext = binary.decode_sixbit_ascii(msgbinary[40:968]).rstrip()

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - from MMSI: {}, '
                   'Message: {}').format(self.description, self.mmsi,
                                         self.msgtext)
        return strtext

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        details = {}
        details['message from'] = self.mmsi
        details['message'] = self.msgtext
        return details
