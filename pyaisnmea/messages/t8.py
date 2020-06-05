import pyaisnmea.binary as binary

import pyaisnmea.messages.aismessage


class Type8BinaryBroadcastMessage(pyaisnmea.messages.aismessage.AISMessage):
    """
    Type 8 - Binary Broadcast Message
    """

    loadstatuses = {0: 'N/A', 1: 'Unloaded', 2: 'Loaded'}
    quality = {0: 'Low', 1: 'High'}
    hazards = {
        0: '0 blue cones/lights',
        1: '1 blue cone/light',
        2: '2 blue cones/lights',
        3: '3 blue cones/lights',
        4: 'B-Flag',
        5: 'Unknown (default)'}
    tendancy = {0: 'steady', 1: 'decreasing', 2: 'increasing', 3: 'N/A'}
    ice = {0: 'no', 1: 'yes', 2: 'reserved for future use', 3: 'not available'}
    beaufort = {0: 'Sea like a mirror',
                1: ('Ripples with appearance of scales are formed,'
                    ' without foam crests'),
                2: ('Small wavelets still short but more pronounced;'
                    ' crests have a glassy appearance but do not break'),
                3: ('Large wavelets; crests begin to break;'
                    ' foam of glassy appearance; '
                    'perhaps scattered white horses'),
                4: 'Small waves becoming longer; fairly frequent white horses',
                5: ('Moderate waves taking a more pronounced long form;'
                    ' many white horses are formed; chance of some spray'),
                6: ('Large waves begin to form; the white foam crests are'
                    ' more extensive everywhere; probably some spray'),
                7: ('Sea heaps up and white foam from breaking waves '
                    'begins to be blown in streaks along the direction '
                    'of the wind; spindrift begins to be seen'),
                8: ('Moderately high waves of greater length; '
                    'edges of crests break into spindrift; foam is blown '
                    'in well-marked streaks along the direction of the wind'),
                9: ('High waves; dense streaks of foam along the direction '
                    'of the wind; sea begins to roll; '
                    'spray affects visibility'),
                10: ('Very high waves with long overhanging crests; '
                     'resulting foam in great patches is blown in dense '
                     'white streaks along the direction of the wind; '
                     'on the whole the surface of the sea takes on a white '
                     'appearance; rolling of the sea becomes heavy; '
                     'visibility affected'),
                11: ('Exceptionally high waves;'
                     ' small- and medium-sized ships might be for a long time '
                     'lost to view behind the waves; sea is covered with long '
                     'white patches of foam; everywhere the edges of the wave '
                     'crests are blown into foam; visibility affected'),
                12: ('The air is filled with foam and spray;'
                     ' sea is completely white with driving spray;'
                     ' visibility very seriously affected'),
                13: 'N/A',
                14: 'N/A',
                15: 'N/A'}
    precipitation = {0: 'Reserved', 1: 'Rain', 2: 'Thunderstorm',
                     3: 'Freezing Rain', 4: 'Mixed/ice', 5: 'Snow',
                     6: 'Reserved', 7: 'N/A'}

    def __init__(self, msgbinary):
        super().__init__(msgbinary)
        self.msgdetails = {}
        self.msgsubtype = 'Unknown'
        self.designatedareacode = self.decode_sixbit_integer(
            msgbinary[40:50])
        self.functionid = self.decode_sixbit_integer(msgbinary[50:56])
        self.identify_subtype()

    def identify_subtype(self):
        """
        Try to identify what sort of Binary Broadcast message this is
        """
        if self.designatedareacode == 200 and self.functionid == 10:
            self.inland_static_and_voyage_data()
        elif self.designatedareacode == 1 and self.functionid == 31:
            self.meteorological_and_hydrological_data()

    def inland_static_and_voyage_data(self):
        """
        sub message type that provides information on Inland Vessels
        """
        self.msgsubtype = 'Inland Static & Voyage Data'
        self.msgdetails['European Vessel ID'] = binary.decode_sixbit_ascii(
            self.msgbinary[56:104])
        self.msgdetails['Length'] = self.decode_sixbit_integer(
            self.msgbinary[104:117]) / 10
        self.msgdetails['Beam'] = self.decode_sixbit_integer(
            self.msgbinary[117:127]) / 10
        self.msgdetails['Ship Type'] = self.decode_sixbit_integer(
            self.msgbinary[127:141])
        self.msgdetails['Hazard'] = self.hazards[self.decode_sixbit_integer(
            self.msgbinary[141:144])]
        self.msgdetails['Draught'] = self.decode_sixbit_integer(
            self.msgbinary[144:155]) / 100
        self.msgdetails['Load Status'] = self.loadstatuses[
            self.decode_sixbit_integer(self.msgbinary[155:157])]
        self.msgdetails['Speed Measurement Quality'] = self.quality[
            self.decode_sixbit_integer(self.msgbinary[157:158])]
        self.msgdetails['Course Measurement Quality'] = self.quality[
            self.decode_sixbit_integer(self.msgbinary[158:159])]
        self.msgdetails['Heading Measurement Quality'] = self.quality[
            self.decode_sixbit_integer(self.msgbinary[159:160])]

    def meteorological_and_hydrological_data(self):
        """
        Weather Data
        """
        self.msgsubtype = 'Meteorological and Hydrological Data'
        self.msgdetails['Position Fix Accuracy'] = self.accuracy[
            self.decode_sixbit_integer(self.msgbinary[105:106])]
        self.msgdetails['Day'] = self.decode_sixbit_integer(
            self.msgbinary[106:111])
        self.msgdetails['Hour'] = self.decode_sixbit_integer(
            self.msgbinary[111:116])
        self.msgdetails['Minute'] = self.decode_sixbit_integer(
            self.msgbinary[116:122])
        self.msgdetails['Average Wind Speed (knots)'] = \
            self.decode_sixbit_integer(self.msgbinary[122:129])
        self.msgdetails['Gust Speed (knots)'] = self.decode_sixbit_integer(
            self.msgbinary[129:136])
        self.msgdetails['Wind Direction'] = self.decode_sixbit_integer(
            self.msgbinary[136:145])
        self.msgdetails['Gust Direction'] = self.decode_sixbit_integer(
            self.msgbinary[145:154])
        self.msgdetails['Air Temperature'] = self.decode_sixbit_integer(
            self.msgbinary[154:165])
        self.msgdetails['Relative Humidity'] = self.decode_sixbit_integer(
            self.msgbinary[165:172])
        self.msgdetails['Dew Point'] = self.decode_sixbit_integer(
            self.msgbinary[172:182])
        self.msgdetails['Air Pressure'] = self.decode_sixbit_integer(
            self.msgbinary[182:191])
        self.msgdetails['Pressure Tendancy'] = self.tendancy[
            self.decode_sixbit_integer(self.msgbinary[191:193])]
        self.msgdetails['Horizontal Visibility'] =  \
            self.decode_sixbit_integer(self.msgbinary[194:201])
        self.msgdetails['Water Level'] = self.decode_sixbit_integer(
            self.msgbinary[201:213])
        self.msgdetails['Water Level Trend'] = self.tendancy[
            self.decode_sixbit_integer(self.msgbinary[213:215])]
        self.msgdetails['Surface Current Speed'] = \
            self.decode_sixbit_integer(self.msgbinary[215:223])
        self.msgdetails['Surface Current Direction'] = \
            self.decode_sixbit_integer(self.msgbinary[223:232])
        self.msgdetails['Current Speed #2'] = self.decode_sixbit_integer(
            self.msgbinary[232:240])
        self.msgdetails['Current Direction #2'] = self.decode_sixbit_integer(
            self.msgbinary[240:249])
        self.msgdetails['Measurement Depth #2'] = self.decode_sixbit_integer(
            self.msgbinary[249:254])
        self.msgdetails['Current Speed #3'] = self.decode_sixbit_integer(
            self.msgbinary[254:262])
        self.msgdetails['Current Direction #3'] = self.decode_sixbit_integer(
            self.msgbinary[262:271])
        self.msgdetails['Measurement Depth #3'] = self.decode_sixbit_integer(
            self.msgbinary[271:276])
        self.msgdetails['Wave Height'] = self.decode_sixbit_integer(
            self.msgbinary[276:284])
        self.msgdetails['Wave Period'] = self.decode_sixbit_integer(
            self.msgbinary[284:290])
        self.msgdetails['Wave Direction'] = self.decode_sixbit_integer(
            self.msgbinary[290:299])
        self.msgdetails['Swell Height'] = self.decode_sixbit_integer(
            self.msgbinary[299:307])
        self.msgdetails['Swell Period'] = self.decode_sixbit_integer(
            self.msgbinary[307:313])
        self.msgdetails['Swell Direction'] = self.decode_sixbit_integer(
            self.msgbinary[313:322])
        self.msgdetails['Sea State'] = self.beaufort[
            self.decode_sixbit_integer(self.msgbinary[322:326])]
        self.msgdetails['Water Temperature'] = self.decode_sixbit_integer(
            self.msgbinary[326:336])
        self.msgdetails['Precipitation'] = self.precipitation[
            self.decode_sixbit_integer(self.msgbinary[336:339])]
        self.msgdetails['Salinity'] = self.decode_sixbit_integer(
            self.msgbinary[339:348])
        self.msgdetails['Ice'] = self.ice[self.decode_sixbit_integer(
            self.msgbinary[348:350])]

    def get_details(self):
        """
        get the most pertinent details of the message as a dictionary

        Returns:
            self.msgdetails(dict): most relevant information of this message
        """
        self.msgdetails['Time'] = self.rxtime
        return {'Binary Message Sub Type':self.msgsubtype,
                'Details': self.msgdetails}

    def __str__(self):
        """
        describes the message object

        Returns:
            strtext(str): string containing information about the message
        """
        strtext = ('{} from - MMSI: {}, Sub Type: {} '
                   'DAC: {}, Function ID: {}').format(self.description,
                                                      self.mmsi,
                                                      self.msgsubtype,
                                                      self.designatedareacode,
                                                      self.functionid)
        return strtext
