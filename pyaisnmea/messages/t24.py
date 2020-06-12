"""
Type 24 messages are used by Class B AIS stations to send information about
the ship. They are similar to Type 5 messages sent by Class A stations.
"""

import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type24StaticDataReport(pyaisnmea.messages.aismessage.AISMessage):
    """
    Used by AIS class B equipment to provide information about the ship.
    Type 5 messages are similar but for class A equipment.

    Note:
        this message is split into 2 subtypes (A & B) identified by the part no

    Attributes:
            partno(int): if zero message is type A, if 1 the message is type B
            name(str): the name of the ship
            shiptype(str): the type of ship - lookup from self.shiptypes
            vendorid(str): identifies equipment manufacturer
            unitmodelcode(int): identifies the specific model
            serialno(int): identifies the actual unit
            callsign(str): VHF marine radio callsign
            length(int): length of the vessel in Metres
            width(int): width of the vessel in Metres
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.partno = self.decode_sixbit_integer(msgbinary[38:40])
        if self.partno == 0:
            self.name = binary.decode_sixbit_ascii(msgbinary[40:160]).rstrip()
        elif self.partno == 1:
            self.shiptype = self.shiptypes[self.decode_sixbit_integer(
                msgbinary[40:48])]
            self.vendorid = binary.decode_sixbit_ascii(msgbinary[48:66])
            self.unitmodelcode = self.decode_sixbit_integer(
                msgbinary[66:70])
            self.serialno = self.decode_sixbit_integer(msgbinary[70:90])
            self.callsign = binary.decode_sixbit_ascii(
                msgbinary[90:132]).rstrip()
            tobow = self.decode_sixbit_integer(msgbinary[240:249])
            tostern = self.decode_sixbit_integer(msgbinary[249:258])
            toport = self.decode_sixbit_integer(msgbinary[258:264])
            tostarboard = self.decode_sixbit_integer(msgbinary[264:270])
            self.length = tobow + tostern
            self.width = toport + tostarboard

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        if self.partno == 0:
            strtext = '{} Type A - MMSI: {}, Name: {}'.format(
                self.description, self.mmsi, self.name)
        elif self.partno == 1:
            strtext = ('{} Type B - MMSI: {}, Ship Type: {},'
                       ' Callsign: {}, Length: {},'
                       ' Width: {}').format(self.description, self.mmsi,
                                            self.shiptype,
                                            self.callsign, self.length,
                                            self.width)
        return strtext

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            details(dict): most relevant information of this message
        """
        details = {}
        if self.partno == 1:
            details['Callsign'] = self.callsign
            details['Ship Type'] = self.shiptype
            details['Width (m)'] = self.width
            details['Length (m)'] = self.length
        return details
