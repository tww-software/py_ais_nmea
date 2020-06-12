"""
Type 6 messages are addressed binary messages.
"""

import pyaisnmea.messages.aismessage


class Type6BinaryMessage(pyaisnmea.messages.aismessage.AISMessage):
    """
    addressed point to point message with unspecified binary payload

    Attributes:
        msgsubtype(str): description of message sub type
        msgdetails(dict): message specific values are stored here
        sequenceno(int): the sequence number
        destinationmmsi(int): the MMSI of who the message is for
        retransmitflag(int): should this be retransmitted?
        designatedareacode(int): DAC use this along with the function id to
                                 identify the type of message encoded within
        functionid(int): helps identify the message within (along with the DAC)
    """

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.msgsubtype = 'Unknown'
        self.msgdetails = {}
        self.sequenceno = self.decode_sixbit_integer(msgbinary[38:40])
        self.destinationmmsi = self.decode_sixbit_integer(msgbinary[40:70])
        self.retransmitflag = self.decode_sixbit_integer(msgbinary[70:71])
        self.designatedareacode = self.decode_sixbit_integer(
            msgbinary[72:82])
        self.functionid = self.decode_sixbit_integer(msgbinary[82:88])
        self.identify_subtype()

    def identify_subtype(self):
        """
        Try to identify what sort of Binary Broadcast message this is
        """
        if self.designatedareacode == 235 and self.functionid == 10:
            self.msgsubtype = 'Aid to Navigation monitoring UK'
            self.navigation_aid_monitoring()
        elif self.designatedareacode == 250 and self.functionid == 10:
            self.msgsubtype = 'Aid to Navigation monitoring ROI'
            self.navigation_aid_monitoring()

    def navigation_aid_monitoring(self):
        """
        used for monitoring of Navigation Aids
        """
        raconstatus = {0: 'no RACON installed', 1: 'RACON not monitored',
                       2: 'RACON operational', 3: 'RACON ERROR'}
        lightstatus = {0: 'no light', 1: 'light on',
                       2: 'light off', 3: 'light ERROR'}
        health = {0: 'good health', 1: 'alarm'}
        posstatus = {0: 'on position', 1: 'off position'}
        self.msgdetails['Analogue'] = self.decode_sixbit_integer(
            self.msgbinary[88:98])
        self.msgdetails['Analogue ext 1'] = self.decode_sixbit_integer(
            self.msgbinary[98:108])
        self.msgdetails['Analogue ext 2'] = self.decode_sixbit_integer(
            self.msgbinary[108:118])
        self.msgdetails['RACON status'] = raconstatus[
            self.decode_sixbit_integer(self.msgbinary[118:120])]
        self.msgdetails['Light status'] = lightstatus[
            self.decode_sixbit_integer(self.msgbinary[120:122])]
        self.msgdetails['Health'] = health[self.decode_sixbit_integer(
            self.msgbinary[122:123])]
        self.msgdetails['Status (external)'] = self.decode_sixbit_integer(
            self.msgbinary[123:131])
        self.msgdetails['Position status'] = posstatus[
            self.decode_sixbit_integer(self.msgbinary[131:132])]

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            msgdetails(dict): most relevant information of this message
        """
        self.msgdetails['Time'] = self.rxtime
        return {'Binary Message Sub Type': self.msgsubtype,
                'Destination MMSI': self.destinationmmsi,
                'Details': self.msgdetails}

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} - {} - MMSI: {}, To: {}, DAC: {}, '
                   'Function ID: {}').format(self.description, self.msgsubtype,
                                             self.mmsi, self.destinationmmsi,
                                             self.designatedareacode,
                                             self.functionid)
        return strtext
