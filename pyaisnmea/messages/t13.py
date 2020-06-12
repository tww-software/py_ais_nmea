"""
Type 13 messages are used to acknowledge safety messages. They are the same
as Type 7 messages.
"""

import pyaisnmea.messages.aismessage


class Type13SafetyAcknowlegement(
        pyaisnmea.messages.t7.Type7BinaryAcknowlegement):
    """
    used to acknowlege safety messages,
    same format as a Type 7 Binary Acknowlegement Message
    """

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
