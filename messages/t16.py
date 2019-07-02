import binary

import messages.aismessage


class Type16AssignmentModeCommand(messages.aismessage.AISMessage):
    """
    NO REAL LIFE TEST DATA FOUND YET!
    """
    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.destinationammsi = binary.decode_sixbit_integer(msgbinary, 40, 70)
        self.offseta = binary.decode_sixbit_integer(msgbinary, 70, 82)
        self.incrementa = binary.decode_sixbit_integer(msgbinary, 82, 92)
        self.destinationbmmsi = binary.decode_sixbit_integer(
            msgbinary, 92, 122)
        self.offsetb = binary.decode_sixbit_integer(msgbinary, 122, 134)
        self.incrementb = binary.decode_sixbit_integer(msgbinary, 134, 144)

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = 'Assignment Mode Command - source MMSI: {}'.format(self.mmsi)
        return strtext
