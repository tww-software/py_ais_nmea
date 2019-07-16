import binary

import messages.aismessage


class Type12AddressedSafetyMessage(messages.aismessage.AISMessage):
    """
    Safety message from one station to another
    """
    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.sequenceno = self.decode_sixbit_integer(msgbinary[38:40])
        self.destinationmmsi = self.decode_sixbit_integer(msgbinary[40:70])
        self.retransmitflag = self.binaryflag[self.decode_sixbit_integer(
            msgbinary[70:71])]
        self.msgtext = binary.decode_sixbit_ascii(msgbinary[72:936]).rstrip()

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - from MMSI: {}, to MMSI: {}, '
                   'Message: {}').format(self.description, self.mmsi,
                                         self.destinationmmsi, self.msgtext)
        return strtext

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        details = {}
        details['message from'] = self.mmsi
        details['message to'] = self.destinationmmsi
        details['retransmit'] = self.retransmitflag
        details['message'] = self.msgtext
        return details
