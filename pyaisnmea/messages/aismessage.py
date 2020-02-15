"""
This file contains the base class for all the different types of AIS messages
that can be decoded.
"""


import pyaisnmea.binary as binary


MSGDESCRIPTIONS = {
    1: 'Type 1 - Position Report Class A',
    2: 'Type 2 - Position Report Class A',
    3: 'Type 3 - Position Report Class A',
    4: 'Type 4 - Base Station Report',
    5: 'Type 5 - Static and Voyage Related Data',
    6: 'Type 6 - Binary Adressed Message',
    7: 'Type 7 - Binary Acknowlegement',
    8: 'Type 8 - Binary Broadcast Message',
    9: 'Type 9 - Standard SAR Aircraft Report',
    10: 'Type 10 - UTC Date Inquiry',
    11: 'Type 11 - UTC Date Response',
    12: 'Type 12 - Addressed Safety Related Message',
    13: 'Type 13 - Safety Related Acknowlegement',
    14: 'Type 14 - Safety Related Broadcast Message',
    15: 'Type 15 - Interrogation',
    16: 'Type 16 - Assignment Mode Command',
    17: 'Type 17 - DGNSS Broadcast Binary Message',
    18: 'Type 18 - Standard Class B CS Position Report',
    19: 'Type 19 - Extended Class B CS Position Report',
    20: 'Type 20 - Datalink Management Message',
    21: 'Type 21 - Aid to Navigation Report',
    22: 'Type 22 - Channel Management',
    23: 'Type 23 - Group Assignment Command',
    24: 'Type 24 - Static Data Report',
    25: 'Type 25 - Single Slot Binary Message',
    26: 'Type 26 - Multiple Slot Binary Message',
    27: 'Type 27 - Long Range AIS Broadcast Message'}


class AISMessage():
    """
    parent class for all the different AIS message types

    Args:
        msgbinary(str): message data as a binary string e.g '011010110101'

    Attributes:
        msgbinary(str): same as argument
        msgtype(int): msg type number
        repeatcount(int): how many times this message should be forwarded on
        mmsi(int): maritime mobile service identifier - unique id of the AIS
                   station who sent the message
    """
    binaryflag = {0: False, 1: True}

    accuracy = {1: '< 10m', 0: '> 10m'}

    dtevalues = {0: 'Data Terminal Ready', 1: 'Not Ready (default)'}

    shiptypes = {0: 'Not available (default)',
                 1: 'Reserved for future use',
                 2: 'Reserved for future use',
                 3: 'Reserved for future use',
                 4: 'Reserved for future use',
                 5: 'Reserved for future use',
                 6: 'Reserved for future use',
                 7: 'Reserved for future use',
                 8: 'Reserved for future use',
                 9: 'Reserved for future use',
                 10: 'Reserved for future use',
                 11: 'Reserved for future use',
                 12: 'Reserved for future use',
                 13: 'Reserved for future use',
                 14: 'Reserved for future use',
                 15: 'Reserved for future use',
                 16: 'Reserved for future use',
                 17: 'Reserved for future use',
                 18: 'Reserved for future use',
                 19: 'Reserved for future use',
                 20: 'Wing in ground (WIG), all ships of this type',
                 21: 'Wing in ground (WIG), Hazardous category A',
                 22: 'Wing in ground (WIG), Hazardous category B',
                 23: 'Wing in ground (WIG), Hazardous category C',
                 24: 'Wing in ground (WIG), Hazardous category D',
                 25: 'Wing in ground (WIG), Reserved for future use',
                 26: 'Wing in ground (WIG), Reserved for future use',
                 27: 'Wing in ground (WIG), Reserved for future use',
                 28: 'Wing in ground (WIG), Reserved for future use',
                 29: 'Wing in ground (WIG), Reserved for future use',
                 30: 'Fishing',
                 31: 'Towing',
                 32: 'Towing: length exceeds 200m or breadth exceeds 25m',
                 33: 'Dredging or underwater ops',
                 34: 'Diving ops',
                 35: 'Military ops',
                 36: 'Sailing',
                 37: 'Pleasure Craft',
                 38: 'Reserved',
                 39: 'Reserved',
                 40: 'High speed craft (HSC), all ships of this type',
                 41: 'High speed craft (HSC), Hazardous category A',
                 42: 'High speed craft (HSC), Hazardous category B',
                 43: 'High speed craft (HSC), Hazardous category C',
                 44: 'High speed craft (HSC), Hazardous category D',
                 45: 'High speed craft (HSC), Reserved for future use',
                 46: 'High speed craft (HSC), Reserved for future use',
                 47: 'High speed craft (HSC), Reserved for future use',
                 48: 'High speed craft (HSC), Reserved for future use',
                 49: 'High speed craft (HSC), No additional information',
                 50: 'Pilot Vessel',
                 51: 'Search and Rescue vessel',
                 52: 'Tug',
                 53: 'Port Tender',
                 54: 'Anti-pollution equipment',
                 55: 'Law Enforcement',
                 56: 'Spare - Local Vessel',
                 57: 'Spare - Local Vessel',
                 58: 'Medical Transport',
                 59: 'Noncombatant ship according to RR Resolution No. 18',
                 60: 'Passenger, all ships of this type',
                 61: 'Passenger, Hazardous category A',
                 62: 'Passenger, Hazardous category B',
                 63: 'Passenger, Hazardous category C',
                 64: 'Passenger, Hazardous category D',
                 65: 'Passenger, Reserved for future use',
                 66: 'Passenger, Reserved for future use',
                 67: 'Passenger, Reserved for future use',
                 68: 'Passenger, Reserved for future use',
                 69: 'Passenger, No additional information',
                 70: 'Cargo, all ships of this type',
                 71: 'Cargo, Hazardous category A',
                 72: 'Cargo, Hazardous category B',
                 73: 'Cargo, Hazardous category C',
                 74: 'Cargo, Hazardous category D',
                 75: 'Cargo, Reserved for future use',
                 76: 'Cargo, Reserved for future use',
                 77: 'Cargo, Reserved for future use',
                 78: 'Cargo, Reserved for future use',
                 79: 'Cargo, No additional information',
                 80: 'Tanker, all ships of this type',
                 81: 'Tanker, Hazardous category A',
                 82: 'Tanker, Hazardous category B',
                 83: 'Tanker, Hazardous category C',
                 84: 'Tanker, Hazardous category D',
                 85: 'Tanker, Reserved for future use',
                 86: 'Tanker, Reserved for future use',
                 87: 'Tanker, Reserved for future use',
                 88: 'Tanker, Reserved for future use',
                 89: 'Tanker, No additional information',
                 90: 'Other Type, all ships of this type',
                 91: 'Other Type, Hazardous category A',
                 92: 'Other Type, Hazardous category B',
                 93: 'Other Type, Hazardous category C',
                 94: 'Other Type, Hazardous category D',
                 95: 'Other Type, Reserved for future use',
                 96: 'Other Type, Reserved for future use',
                 97: 'Other Type, Reserved for future use',
                 98: 'Other Type, Reserved for future use',
                 99: 'Other Type, no additional information'}

    epfdfixtypes = {0: 'Undefined (default)',
                    1: 'GPS',
                    2: 'GLONASS',
                    3: 'Combined GPS/GLONASS',
                    4: 'Loran-C',
                    5: 'Chayka',
                    6: 'Integrated navigation system',
                    7: 'Surveyed',
                    8: 'Galileo',
                    15: 'Undefined'}

    navstatustypes = {0: 'Under way using engine',
                      1: 'At anchor',
                      2: 'Not under command',
                      3: 'Restricted manoeuverability',
                      4: 'Constrained by her draught',
                      5: 'Moored',
                      6: 'Aground',
                      7: 'Engaged in Fishing',
                      8: 'Under way sailing',
                      9: 'Reserved for future amendment of Navigational Status'
                         ' for HSC',
                      10: 'Reserved for future amendment of Navigational '
                          'Status for WIG',
                      11: 'Reserved for future use',
                      12: 'Reserved for future use',
                      13: 'Reserved for future use',
                      14: 'AIS-SART is active',
                      15: 'Not defined (default)'}

    def __init__(self, msgbinary):
        self.msgbinary = msgbinary
        self.msgtype = binary.decode_sixbit_integer(msgbinary[0:6])
        self.repeatcount = binary.decode_sixbit_integer(msgbinary[6:8])
        self.mmsi = str(format(binary.decode_sixbit_integer(msgbinary[8:38]),
                           '09d'))
        self.details = {}
        self.positiondata = {}
        try:
            self.description = MSGDESCRIPTIONS[self.msgtype]
        except KeyError:
            self.description = 'Unknown'
        self.rxtime = 'N/A'

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('Unspecified AIS message - MMSI: {}, '
                   'Message Type: {}').format(self.mmsi, self.msgtype)
        return strtext

    def __repr__(self):
        reprstr = '{}.("{}")'.format(self.__class__.__name__, self.msgbinary)
        return reprstr

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        raise NotImplementedError('this method should return a dictionary'
                                  'containing useful info from the message')

    def get_position_data(self):
        """
        get the position data from this message

        Returns:
            posrep(dict): position and navigation details from the message
        """
        raise NotImplementedError('this method should return a dictionary'
                                  'containing position info from the message')

    def return_payload(self):
        """
        helper method to calculate the payload that generated this message

        Returns:
            payload(str): the NMEA 0183 payload of this message
        """
        payload = binary.ais_sentence_binary_payload(self.msgbinary)
        return payload

    @staticmethod
    def decode_sixbit_integer(binarystr):
        """
        a wrapper for binary.decode_sixbit_intger
        adds exception handling

        Note:
            if we get a no binary data exception simply return a 0
        """
        try:
            returnval = binary.decode_sixbit_integer(binarystr)
        except binary.NoBinaryData:
            returnval = 0
        return returnval
