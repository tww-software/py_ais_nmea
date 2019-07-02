"""
Unit tests for the AIS Decoder
"""

# pylint: disable=no-member
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import datetime
import os
import unittest

import ais
import binary
import geojson
import icons
import nmea
import messages
import messages.aismessage
import messages.t123
import messages.t4
import messages.t5
import messages.t6
import messages.t7
import messages.t8
import messages.t9
import messages.t10
import messages.t11
import messages.t12
import messages.t13
import messages.t14
import messages.t15
import messages.t16
import messages.t17
import messages.t18
import messages.t19
import messages.t20
import messages.t21
import messages.t22
import messages.t23
import messages.t24
import messages.t25
import messages.t26
import messages.t27

class BinaryTests(unittest.TestCase):
    """
    tests related to decoding binary data
    """

    def test_NMEA_to_binary_string(self):
        """
        Tests converting a sixbit ascii string into a binary string.
        """
        testpayload = 'E>jHC=c6:W2h22R`@1:WdP00000Opa@H?KTcP10888e?B0'
        expectedbinary = ('01010100111011001001100001001100'
                          '11011010110001100010101001110000'
                          '10110000000010000010100010101000'
                          '01000000000100101010011110110010'
                          '00000000000000000000000000000000'
                          '00011111111000101001010000011000'
                          '00111101101110010010101110000000'
                          '00010000000010000010000010001011'
                          '01001111010010000000')

        binresult = binary.ais_sentence_payload_binary(testpayload)
        self.assertEqual(binresult, expectedbinary)

    def test_ASCII_decode(self):
        """
        Tests converting a binary string into readable text.
        """
        testbinarystr = ('010100001000000101100000010001010101001001000011'
                         '001011100000000010010010001111010111001110'
                         '100000000110001111011000100000001010010101'
                         '001101010000010011100000001111010110000101'
                         '010010100000010100001000000101100000001100'
                         '000001011010011001100000000100001111000111'
                         '100000110000110001110010110011110100110101'
                         '110110110111111000111001')
        expectedstr = 'THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG 0123456789'
        resultstr = binary.decode_sixbit_ascii(testbinarystr, 0, 324)
        self.assertEqual(expectedstr, resultstr)

    def test_binary_string_to_NMEA_payload(self):
        """
        tests converting a binary string back into its NMEA 0183 payload
        """
        expectedpayload = '402=acAv=6;4cwi3FHNPPTW005H@'
        binresult = binary.ais_sentence_payload_binary(expectedpayload)
        testpayload = binary.ais_sentence_binary_payload(binresult)
        self.assertEqual(expectedpayload, testpayload)

    def test_sixbit_integer_decoding(self):
        """
        tests converting from binary into integer
        """
        binstr = '000001100'
        expected = 12
        decoded = binary.decode_sixbit_integer(binstr, 2, 9)
        self.assertEqual(expected, decoded)


class NMEATests(unittest.TestCase):
    """
    tests related to the interpretation of AIS NMEA 0183 sentences
    """

    def test_nmea_stats(self):
        """
        feed in NMEA sentences and check that stats are computed correctly
        """
        testsentences = [
            '!AIVDM,1,1,,A,13P6>F002lwce04NvkaT<CPGH<02,0*69',
            '!AIVDM,1,1,,A,13P6>F002jwceJDNvk1T<SPcH8Og,0*2F',
            '!AIVDM,1,1,,A,13P6>F002kwcf6dNvj0T=kQ?H@3Q,0*27',
            ('!AIVDM,2,1,5,A,53P6>F42;si4mPhOJ208Dr0mV0<Q8DF22222'
             '220t41H;==8cN<R1FDj0,0*39'),
            '!AIVDM,2,2,5,A,CH8888888888880,2*2A',
            '!AIVDM,1,1,,A,13P6>F002lwcfRPNviF4;CQUH8:s,0*72',
            '!AIVDM,1,1,,B,33P6>F002lwcfgDNvi4T>SQgH50S,0*40',
            '!AIVDM,1,1,,B,13P6>F002lwcg8`NvhLT>kP;HL02,0*3C']
        testtracker = nmea.NMEAtracker()
        for sentence in testsentences:
            processed = testtracker.process_sentence(sentence)
        teststats = testtracker.nmea_stats()
        expectedstats = {'Total Sentences Processed': 8,
                         'Multipart Messages Reassembled': 1,
                         'Messages Recieved on Channel': {'A': 6, 'B': 2}}
        self.assertDictEqual(teststats, expectedstats)

    def test_correct_nmea_checksum(self):
        """
        feed in an NMEA 0183 sentence and calculate its checksum
        checksum should be correct and True
        """
        testsentence = ('!AIVDM,1,1,,B,E>jHC=c6:W2h22R`@1:WdP00000Opa'
                        '@F?KTa010888e?B0,0*72')
        self.assertTrue(nmea.calculate_nmea_checksum(testsentence))

    def test_incorrect_nmea_checksum(self):
        """
        feed in an NMEA 0183 sentence and calculate its checksum
        checksum should be incorrect and False
        """
        testsentence = ('!AIVDM,1,1,,B,E>jHC=c6:W2h22R`@1:WdP00000Opa'
                        '@F?KTa010888e?B0,0*75')
        self.assertFalse(nmea.calculate_nmea_checksum(testsentence))

    def test_other_nmea_sentence(self):
        """
        the calculate checksum method can be used with other types of NMEA
        sentences
        """
        testsentence = ('$GPRMC,152904.000,A,4611.1699,N,00117.8182,'
                        'W,000.00,0.0,240714,,,E*46')
        self.assertTrue(nmea.calculate_nmea_checksum(testsentence, start='$'))

    def test_nmea_sentence_regex_match(self):
        """
        test the regex that matches NMEA 0183 sentences
        """
        testsentence = ('!AIVDM,1,1,,A,E>jHC=c6:W2h22R`@1:WdP00000Opa@B?KT'
                        '`P10888e?N0,0*18')
        self.assertRegex(testsentence, nmea.NMEASENTENCEREGEX)

    def test_nmea_sentence_regex_notmatching(self):
        """
        regex should not match, improperly formatted NMEA sentence

        Note:
            there are 3 hyphens and an underscore in the payload
            the channel no is invalid
            the checksum is correct
        """
        testsentence = '!AIVDM,1,1,,3,E>jHC---_pa@Q?KTa010888e?B0,0*5C'
        self.assertNotRegex(testsentence, nmea.NMEASENTENCEREGEX)

    def test_nmea_multipart_sentence_reassembly(self):
        """
        test the ability to recieve multiple NMEA 0183 sentences and join
        them together into one AIS message
        """
        expected = ('000101000011000111100001100010000000000'
                    '10000001001001111000100100011001'
                    '1010100001001100000111011010010000010000'
                    '000011000100100010000010100110'
                    '0001001001111100000100000100000100000100000'
                    '10000010000010000010000010000010000010000010'
                    '00000101100100101000000001100000111100001000'
                    '010011100010011100000001001111000010000001010'
                    '010010010000101001001010010001111100000100000'
                    '100000100000100000100000100000100000100000100'
                    '0001000001000000000')
        testsentences = [
            ('!AIVDM,2,1,2,B,537QR042Ci8kD9PsB20HT'
             '@DhTv2222222222221I:0H?24pW0ChPDTQB,0*49'),
            '!AIVDM,2,2,2,B,DSp888888888880,2*7A']
        testtracker = nmea.NMEAtracker()
        for sentence in testsentences:
            processed = testtracker.process_sentence(sentence)
            if processed:
                binarypayload = binary.ais_sentence_payload_binary(processed)
        self.assertEqual(expected, binarypayload)


class AISStationTests(unittest.TestCase):
    """
    tests related to AIS message types and interpretting AIS data at the higher
    levels
    """
    def setUp(self):
        self.aisteststn = ais.AISStation('123456789')

    def test_no_position_information(self):
        """
        create a new AIS station object to respresent a AIS transmitter
        try to grab its last known location
        this should return 'unknown' as we havn't given it any LATLON coords
        """
        lastpos = self.aisteststn.get_latest_position()
        self.assertEqual(lastpos, 'Unknown')

    def test_unknown_flag_identification(self):
        """
        the ships flag can be determined from its MMSI
        as the MMSI we have given isn't real and no country uses 123 as its
        MID (maritime identification digits) the .flag attribute should be
        'Unknown'
        """
        self.assertEqual(self.aisteststn.flag, 'Unknown')

    def test_position_update(self):
        """
        in this test we will add some LAT LON coords to our AISStation object
        and then retrieve the last one
        """
        expectedpos = {'Latitude': 53.90606666666667,
                       'Longitude': -3.3356966666666668}
        positions = [
            [53.864983333333335, -4.328763333333334],
            [53.90793333333333, -3.6327133333333332],
            [53.90606666666667, -3.3356966666666668]]
        for posrep in positions:
            self.aisteststn.update_position(posrep[0], posrep[1])
        lastpos = self.aisteststn.get_latest_position()
        self.assertEqual(lastpos, expectedpos)


class AISStationTestsRealData(unittest.TestCase):
    """
    tests using real life test data
    """

    def setUp(self):
        self.aisteststn = ais.AISStation('235070199')

    def test_identify_flag(self):
        """
        we can identify the flag from the MMSI
        """
        expect = "United Kingdom"
        self.assertEqual(expect, self.aisteststn.flag)

    def test_position_update_from_messages(self):
        """
        use actual recieved messages to update the position
        """
        posreps = ['13P;Ruhvj1wj=0bNTU;up;=T80Rd',
                   '13P;RuhvjIwj7blNUOPtIr1n8000',
                   '13P;RuhvjUwivdfNV=7dL:2t80Rd',
                   '13P;RuhsCfwihvnNWpTtLb0<8@3p']
        for pos in posreps:
            binarystr = binary.ais_sentence_payload_binary(pos)
            posmsg = messages.t123.Type123PositionReportClassA(binarystr)
            self.aisteststn.find_position_information(posmsg)
        self.assertEqual(len(posreps), len(self.aisteststn.posrep))

    def test_find_station_name_and_subtype(self):
        """
        get the name and ship type from a Type 5 Static Data Report
        """
        t5payload = ('53P;Rul2<10S89PgN20l4p4pp4r222222222220'
                     '`8@N==57nN9A3mAk0Dp8888888888880')
        expect = {'name': 'MANANNAN',
                  'subtype': 'High speed craft (HSC), all ships of this type'}
        t5binary = binary.ais_sentence_payload_binary(t5payload)
        t5obj = messages.t5.Type5StaticAndVoyageData(t5binary)
        self.aisteststn.find_station_name_and_subtype(t5obj)
        found = {'name': self.aisteststn.name,
                 'subtype': self.aisteststn.subtype}
        self.assertDictEqual(expect, found)


class AISTrackerTests(unittest.TestCase):
    """
    test the AIS tracker and how it can identify and
    keep track of multiple AIS stations
    """
    def setUp(self):
        self.aistracker = ais.AISTracker()

    def process_sentence(self, payload):
        """
        take a nmea sentence decode the payload and pass it to the
        ais tracker

        Args:
            payload(str): AIS nmea 0183 sentence payload encoded in 6 bit ascii

        Returns:
            msgobj(messages.aismessage.AISMessage): AIS message object
                                                    depends on message type
        """
        msgobj = self.aistracker.process_message(payload)
        return msgobj

    def test_classA_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '13;0vj5P2NwiR@HN`Buk<OwF0D1M'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t123.Type123PositionReportClassA)

    def test_base_station_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '402=a`1v:Dg>pOi>SlNu0wQ02HQ='
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t4.Type4BaseStationReport)

    def test_static_and_voyage_data(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = ('53P6>F42;si4mPhOJ208Dr0mV0<Q8DF22222220t41H'
                        ';=6DhN<Q3mAk0Dp8888888888880')
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t5.Type5StaticAndVoyageData)

    def test_binary_message(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '63P<lmL0SJJl01lSrjQC<qEK?00100800h<00mt<003`s9AK00'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t6.Type6BinaryMessage)

    def test_binary_ack(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '7@2=ac@p3HgD'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t7.Type7BinaryAcknowlegement)

    def test_binary_broadcast(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '83P=pSPj2`8800400PPPM00M5fp0'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t8.Type8BinaryBroadcastMessage)

    def test_SAR_aircraft_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '91b56327QgwcN<HNM5b52uP240S4'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(
            msg, messages.t9.Type9StandardSARAircraftPositionReport)

    def test_UTC_date_request(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = ':5Tjep1CuGPP'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t10.Type10UTCDateInquiry)

    def test_UTC_date_response(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = ';3NEKV1v:Dfc`wj=u@NS50A00000'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t11.Type11UTCDateResponse)

    def test_safety_acknowlegement(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '=5e31d00pp1@'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t13.Type13SafetyAcknowlegement)

    def test_interrogation(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '?3P=A400SJJl@00'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t15.Type15Interrogation)

    def test_classB_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'B3P7uL@00OtgPR7fFLTvGwo5oP06'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t18.Type18PositionReportClassB)

    def test_extended_classB_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'C3P8A>@007tgWa7fF6`00000P2>:`W0H28k111111110B0D2Q120'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t19.Type19ExtendedReportClassB)

    def test_datalink_management_message(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'D02PedQV8N?b<`N000'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(
            msg, messages.t20.Type20DatalinkManagementMessage)

    def test_naviagation_aid(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'E>jHC=c6:W2h22R`@1:WdP00000Op`t;?KTs@10888e?N0'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t21.Type21AidToNavigation)

    def test_static_data_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'H3P7uLAT58tp400000000000000'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, messages.t24.Type24StaticDataReport)

    def test_long_range_AIS_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'K5US7R0Oov3rg0F8'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(
            msg, messages.t27.Type27LongRangeAISPositionReport)


class Type8BinaryMessageTests(unittest.TestCase):
    """
    test being able to distinquish between different types of Type 8 messages
    """

    def test_inland_static_and_voyage_data(self):
        payload = '83P=pSPj2`8800400PPPM00M5fp0'
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = messages.t8.Type8BinaryBroadcastMessage(msgbinary)
        self.assertEqual(msg.msgsubtype, 'Inland Static & Voyage Data')

    def test_meteorological_and_hydrological_data(self):
        payload = '8>jHC700Gwn;21S`2j2ePPFQDB06EuOwgwl?wnSwe7wvlO1PsAwwnSAEwvh0'
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = messages.t8.Type8BinaryBroadcastMessage(msgbinary)
        self.assertEqual(msg.msgsubtype, 'Meteorological and Hydrological Data')


class Type6BinaryMessageTests(unittest.TestCase):
    """
    test being able to distinquish between different types of Type 6 messages
    """

    def test_navigation_aid_monitoring_UK(self):
        payload = '6>jHC700V:C0>da6TPAvP00'
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = messages.t6.Type6BinaryMessage(msgbinary)
        self.assertEqual(msg.msgsubtype, 'Aid to Navigation monitoring UK')

    def test_navigation_aid_monitoring_ROI(self):
        payload = '6>jHC7D0V:C0?``00000P00i'
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = messages.t6.Type6BinaryMessage(msgbinary)
        self.assertEqual(msg.msgsubtype, 'Aid to Navigation monitoring ROI')


class AISTrackerTimingTests(unittest.TestCase):
    """
    test how the aistracker class handles times from timestamps both
    recieved and generated locally
    """

    def setUp(self):
        self.aistracker = ais.AISTracker()

    def test_invalid_times_from_base_station(self):
        """
        Tests giving invalid times to the aistracker so it won't be
        able to find a start and finish time.
        """
        expected = 'No time data available.'
        timings = [
            '402=acP000HttwhRddNPs;G00l1G',
            '402=acP000HttwhRddNPs;G00p4E',
            '402=acP000HttwhRddNPs;G00t1H',
            '402=acP000HttwhRddNPs;G00UhP']
        for data in timings:
            self.aistracker.process_message(data)
        stats = self.aistracker.all_station_info()
        self.assertEqual(expected, stats['Times'])

    def test_valid_times_from_base_station(self):
        """
        Tests the aistracker figuring out the start and finish time from
        base station reports that have been recieved.
        """
        expected = {
            "Started": "20180909_140714",
            "Finished": "20180909_142006"}
        timings = [
            '402=aeQv:Df7>whRv`NPsHg005hL',
            '402=a`1v:Df:@Oi>SjNu0si02H9i',
            '4>jHCviv:Df@WOfG8fNQ6io008GL',
            '402=a`1v:DfD6Oi>SpNu0t102@3r']
        for data in timings:
            self.aistracker.process_message(data)
        stats = self.aistracker.all_station_info()
        self.assertDictEqual(expected, stats['Times'])

    def test_live_times(self):
        """
        Tests live timestamps provided at the same time as the NMEA payload
        is given to the AIS tracker class for processing
        """
        payloads = [
            '13P6>F002bwhDQ:NbBIdAqmeH5pl',
            'E>jHC=c6:W2h22R`@1:WdP00000Opa@a?KTP010888e?N0',
            '13P;Ruhvh0wjA=NNSjD:C500880L']
        times = []
        for data in payloads:
            currenttime = datetime.datetime.now()
            times.append(currenttime)
            self.aistracker.process_message(
                data, timestamp=currenttime)
        self.assertEqual(times, self.aistracker.timings)


class GeoJSONTests(unittest.TestCase):
    """
    testing the creation of GeoJSON
    """

    def setUp(self):
        self.parser = geojson.GeoJsonParser()

    def test_add_station_info(self):
        """
        Tests adding data for a new station.
        """
        expected = {
            'type': 'FeatureCollection',
            'features': [{'type': 'Feature',
                          'geometry': {'type': 'Point',
                                       'coordinates': [-3.3356966666666668,
                                                       53.90606666666667]},
                          'properties': {'MMSI': '123456789',
                                         'Type': 'not specified',
                                         'Flag': 'unknown'}},
                         {'type': 'Feature',
                          'geometry': {'type': 'LineString',
                                       'coordinates': [[-4.328763333333334,
                                                        53.864983333333335],
                                                       [-3.6327133333333332,
                                                        53.90793333333333],
                                                       [-3.3356966666666668,
                                                        53.90606666666667]]},
                          'properties': {'MMSI': '123456789'}}]}
        mmsi = '123456789'
        positions = [
            [-4.328763333333334, 53.864983333333335],
            [-3.6327133333333332, 53.90793333333333],
            [-3.3356966666666668, 53.90606666666667]]
        lon = positions[2][0]
        lat = positions[2][1]
        properties = {'Flag': 'unknown', 'Type': 'not specified', 'MMSI': mmsi}
        self.parser.add_station_info(mmsi, properties, positions, lon, lat)
        self.assertEqual(expected, self.parser.main)

    def test_feature_point(self):
        """
        Tests adding a point on the map.
        """
        testinfo = {'Name': 'Blackpool Tower', 'Height(m)': 158}
        testlat = 53.815964
        testlon = -3.055468
        expected = {"type": "Feature",
                    "geometry": {"type": "Point",
                                 "coordinates": [testlon, testlat]},
                    "properties": testinfo}
        returned = self.parser.create_feature_point(testlon, testlat, testinfo)
        self.assertEqual(expected, returned)

    def test_feature_linestring(self):
        """
        Tests adding a line on the map.
        """
        positions = [
            [-4.328763333333334, 53.864983333333335],
            [-3.6327133333333332, 53.90793333333333],
            [-3.3356966666666668, 53.90606666666667]]
        testinfo = {'description': 'coords in Morcambe Bay'}
        expected = {"type": "Feature", "geometry": {"type": "LineString",
                                                    "coordinates": positions},
                    "properties": testinfo}
        returned = self.parser.create_feature_linestring(positions, testinfo)
        self.assertEqual(expected, returned)


class IconTests(unittest.TestCase):
    """
    check the icons are correct and accessible
    """

    def test_icons_exist(self):
        """
        check the icon files are in the correct location, tests that the number
        of icons in the icons folder is the same as in the icons.ICONS dict
        """
        exists = 0
        iconspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'static', 'icons')
        for vesselname in icons.ICONS:
            if os.path.exists(os.path.join(iconspath,
                                           icons.ICONS[vesselname])):
                exists += 1
        self.assertEqual(len(icons.ICONS), exists)


if __name__ == '__main__':
    unittest.main()
