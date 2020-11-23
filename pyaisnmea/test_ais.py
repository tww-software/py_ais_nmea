"""
Unit tests for the AIS Decoder
"""

# pylint: disable=no-member
# pylint: disable=import-error
# pylint: disable=no-name-in-module
# pylint: disable=invalid-name


import datetime
import os
import unittest
import xml.etree.ElementTree

import pyaisnmea.ais as ais
import pyaisnmea.binary as binary
import pyaisnmea.export as export
import pyaisnmea.geojson as geojson
import pyaisnmea.icons as icons
import pyaisnmea.kml as kml
import pyaisnmea.nmea as nmea
import pyaisnmea.messages.t123 as t123
import pyaisnmea.messages.t4 as t4
import pyaisnmea.messages.t5 as t5
import pyaisnmea.messages.t6 as t6
import pyaisnmea.messages.t7 as t7
import pyaisnmea.messages.t8 as t8
import pyaisnmea.messages.t9 as t9
import pyaisnmea.messages.t10 as t10
import pyaisnmea.messages.t11 as t11
import pyaisnmea.messages.t12 as t12
import pyaisnmea.messages.t13 as t13
import pyaisnmea.messages.t14 as t14
import pyaisnmea.messages.t15 as t15
# import pyaisnmea.messages.t16 as t16
import pyaisnmea.messages.t17 as t17
import pyaisnmea.messages.t18 as t18
import pyaisnmea.messages.t19 as t19
import pyaisnmea.messages.t20 as t20
import pyaisnmea.messages.t21 as t21
# import pyaisnmea.messages.t22 as t22
# import pyaisnmea.messages.t23 as t23
# import pyaisnmea.messages.t24 as t24
# import pyaisnmea.messages.t25 as t25
# import pyaisnmea.messages.t26 as t26
import pyaisnmea.messages.t27 as t27


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
        resultstr = binary.decode_sixbit_ascii(testbinarystr[0:324])
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
        decoded = binary.decode_sixbit_integer(binstr[2:9])
        self.assertEqual(expected, decoded)

    def test_empty_value_for_cog(self):
        """
        this sentence doesn't appear to have a value for course over ground
        the binary module should raise a NoBinaryData exception
        """
        testsentence = '!AIVDM,1,1,,A,3O>soN5MUNBoMdUdlh,0*64'
        nmeatracker = nmea.NMEAtracker()
        testdata = nmeatracker.process_sentence(testsentence)
        testbinarystr = binary.ais_sentence_payload_binary(testdata)
        with self.assertRaises(binary.NoBinaryData):
            binary.decode_sixbit_integer(testbinarystr[116:128]) / 10

    def test_empty_string_ais_sentence_payload_binary(self):
        """
        an empty string should raise a NoBinaryData exception
        """
        with self.assertRaises(binary.NoBinaryData):
            binary.ais_sentence_payload_binary('')

    def test_empty_string_ais_sentence_binary_payload(self):
        """
        an empty string should raise a NoBinaryData exception
        """
        with self.assertRaises(binary.NoBinaryData):
            binary.ais_sentence_binary_payload('')

    def test_empty_string_decode_sixbit_ascii(self):
        """
        an empty string should raise a NoBinaryData exception
        """
        with self.assertRaises(binary.NoBinaryData):
            binary.decode_sixbit_ascii('')

    def test_empty_string_decode_twos_complement(self):
        """
        an empty string should raise a NoBinaryData exception
        """
        with self.assertRaises(binary.NoBinaryData):
            binary.decode_twos_complement('')


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
            testtracker.process_sentence(sentence)
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
        with self.assertRaises(ais.NoSuitablePositionReport):
            self.aisteststn.get_latest_position()

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
            self.aisteststn.update_position({'Latitude': posrep[0],
                                             'Longitude': posrep[1]})
        lastpos = self.aisteststn.get_latest_position()
        self.assertEqual(lastpos, expectedpos)

    def test_no_latitiude(self):
        """
        submit a position report with no latitude
        """
        with self.assertRaises(ais.NoSuitablePositionReport):
            posrep = [91.0, -4.132333333332]
            self.aisteststn.update_position({'Latitude': posrep[0],
                                             'Longitude': posrep[1]})

    def test_no_longitude(self):
        """
        submit a position report with no longitude
        """
        with self.assertRaises(ais.NoSuitablePositionReport):
            posrep = [53.8923333333, 181.0]
            self.aisteststn.update_position({'Latitude': posrep[0],
                                             'Longitude': posrep[1]})

    def test_no_longitude_no_latitiude(self):
        """
        submit a position report with no longitude or latitude
        """
        with self.assertRaises(ais.NoSuitablePositionReport):
            posrep = [91.0, 181.0]
            self.aisteststn.update_position({'Latitude': posrep[0],
                                             'Longitude': posrep[1]})


class AISStationTestsRealData(unittest.TestCase):
    """
    tests using real life test data
    """

    def setUp(self):
        self.aisteststn = ais.AISStation('235070199')

    def test_get_station_info(self):
        """
        test for getting useful info from the station object

        this will be pretty empty as we havn't added any position reports or
        voyage data yet!
        """
        stninfodict = self.aisteststn.get_station_info(verbose=True)
        expected = {'MMSI': '235070199', 'Class': 'Unknown', 'Type': 'Unknown',
                    'Flag': 'United Kingdom', 'Name': '',
                    'Position Reports': [],
                    'Sent Messages': {}}
        self.assertDictEqual(stninfodict, expected)

    def test_stn_str(self):
        """
        test object str format
        """
        expected = ('AIS Station - MMSI: 235070199, Name: , Class: Unknown,'
                    ' Type: Unknown, Flag: United Kingdom')
        teststr = self.aisteststn.__str__()
        self.assertEqual(expected, teststr)

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
            posmsg = t123.Type123PositionReportClassA(binarystr)
            self.aisteststn.find_position_information(posmsg)
        self.assertEqual(len(posreps), len(self.aisteststn.posrep))

    def test_find_station_name_and_type(self):
        """
        get the name and ship type from a Type 5 Static Data Report
        """
        t5payload = ('53P;Rul2<10S89PgN20l4p4pp4r222222222220'
                     '`8@N==57nN9A3mAk0Dp8888888888880')
        expect = {'name': 'MANANNAN',
                  'stntype': 'High speed craft (HSC), all ships of this type'}
        t5binary = binary.ais_sentence_payload_binary(t5payload)
        t5obj = t5.Type5StaticAndVoyageData(t5binary)
        self.aisteststn.find_station_name_and_type(t5obj)
        found = {'name': self.aisteststn.name,
                 'stntype': self.aisteststn.stntype}
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
            msgobj(aismessage.AISMessage): AIS message object
                                                    depends on message type
        """
        msgobj = self.aistracker.process_message(payload)
        return msgobj

    def test_all_zeros_mmsi(self):
        """
        this message was sent from a stn that has a MMSI of all zeros
        an Invalif MMSI exception should be raised
        """
        testsentence = '7000003dTni4'
        with self.assertRaises(ais.InvalidMMSI):
            self.process_sentence(testsentence)

    def test_unknown_message(self):
        """
        This is an unknown message, random letters we made up
        an Unknown Message exception should be raised
        """
        testsentence = 'NHIV000IhO9ftkdhwh'
        with self.assertRaises(ais.UnknownMessageType):
            self.process_sentence(testsentence)

    def test_classA_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '13;0vj5P2NwiR@HN`Buk<OwF0D1M'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t123.Type123PositionReportClassA)

    def test_base_station_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '402=a`1v:Dg>pOi>SlNu0wQ02HQ='
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t4.Type4BaseStationReport)

    def test_static_and_voyage_data(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = ('53P6>F42;si4mPhOJ208Dr0mV0<Q8DF22222220t41H'
                        ';=6DhN<Q3mAk0Dp8888888888880')
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t5.Type5StaticAndVoyageData)

    def test_binary_message(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '63P<lmL0SJJl01lSrjQC<qEK?00100800h<00mt<003`s9AK00'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t6.Type6BinaryMessage)

    def test_binary_ack(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '7@2=ac@p3HgD'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t7.Type7BinaryAcknowlegement)

    def test_binary_broadcast(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '83P=pSPj2`8800400PPPM00M5fp0'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t8.Type8BinaryBroadcastMessage)

    def test_SAR_aircraft_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '91b56327QgwcN<HNM5b52uP240S4'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(
            msg, t9.Type9StandardSARAircraftPositionReport)

    def test_UTC_date_request(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = ':5Tjep1CuGPP'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t10.Type10UTCDateInquiry)

    def test_UTC_date_response(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = ';3NEKV1v:Dfc`wj=u@NS50A00000'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t11.Type11UTCDateResponse)

    def test_addressed_safety_message(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '<778Vo1E5r5PD5CD'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t12.Type12AddressedSafetyMessage)

    def test_safety_acknowlegement(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '=5e31d00pp1@'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t13.Type13SafetyAcknowlegement)

    def test_safety_broadcast(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '>37POV1@E=B0Hn05<4hV10i>04<d'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t14.Type14SafetyBroadcastMessage)

    def test_interrogation(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = '?3P=A400SJJl@00'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t15.Type15Interrogation)

    def test_DGNSS_binary_broadcast(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = ('A03n9r0MFhOC00@0f;EV302K4ih20:'
                        'cj7QT0AwlV1Ovb2QtM04`4FQP0EwmG1gpWuB2b')
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg,
                              t17.Type17DGNSSBroadcastBinaryMessage)

    def test_classB_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'B3P7uL@00OtgPR7fFLTvGwo5oP06'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t18.Type18PositionReportClassB)

    def test_extended_classB_position_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'C3P8A>@007tgWa7fF6`00000P2>:`W0H28k111111110B0D2Q120'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t19.Type19ExtendedReportClassB)

    def test_datalink_management_message(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'D02PedQV8N?b<`N000'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(
            msg, t20.Type20DatalinkManagementMessage)

    def test_naviagation_aid(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'E>jHC=c6:W2h22R`@1:WdP00000Op`t;?KTs@10888e?N0'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(msg, t21.Type21AidToNavigation)

    def test_static_data_report_typeA(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'H3P7uLAT58tp400000000000000'
        msg = self.process_sentence(testsentence)
        self.assertEqual(msg.name, 'YARONA')

    def test_static_data_report_typeB(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'H3P7uLDT4I138D0FA=;l001`0310'
        msg = self.process_sentence(testsentence)
        self.assertEqual(msg.callsign, 'VQMK4')

    def test_long_range_AIS_report(self):
        """
        Test to see if a particular message type is recognised
        """
        testsentence = 'K5US7R0Oov3rg0F8'
        msg = self.process_sentence(testsentence)
        self.assertIsInstance(
            msg, t27.Type27LongRangeAISPositionReport)


class AISTrackerandStationTests(unittest.TestCase):
    """
    use an AIS Tracker object to feed in real AIS data and test the AIS
    Station Objects are processing them correctly
    """
    def setUp(self):
        self.aistracker = ais.AISTracker()

    def feed_in_sentences_to_tracker(self, sentences):
        """
        feed sentences into the ais tracker object

        Args:
            sentences(list): list of sentences as strings
        """
        for sentence in sentences:
            self.aistracker.process_message(sentence)

    def test_identify_SAR_aircraft_from_msgtype(self):
        """
        Can we identify an SAR aircraft if the MMSI is not in the expected
        format
        """
        sentences = ['93fK5Slj1VOGD`hMS1iHR2P205k<',
                     '93fK5SlmQTOG@f`MRWJHIr020@HE',
                     '93fK5Slmi`OG8P<MQjApQJ020<0w',
                     '93fK5SlmiVOG1ivMQ49`PGh208C0']
        self.feed_in_sentences_to_tracker(sentences)
        stn = self.aistracker.stations['250004879']
        self.assertEqual(stn.stntype, 'SAR Aircraft')

    def test_destination_changes(self):
        """
        feed in two type 5 messages with different ETA and Destinations
        """
        sentences = ['13P;Ruh1E1wemoRNrlDsEa9l8pRQ',
                     ('53P;Rul2<10S89PgN20l4p4pp4r222222222220`'
                      '8@N==5J?09A3mAk0Dp8888888888880'),
                     '13P;Ruh1DqweQ>pNsH=cE97l8Uhl',
                     ('53P;Rul2<10S89PgN20l4p4pp4r222222222220`'
                      '8@N==5Jc09B1FDj0CH8888888888880'),
                     '13P;Rum000wcR72Nvtnq;3IL8RjH']
        self.feed_in_sentences_to_tracker(sentences)
        stn = self.aistracker.stations['235070199']
        destinations = [
            stn.posrep[1]['Destination'], stn.posrep[2]['Destination']]
        expected = ['DOUGLAS', 'HEYSHAM']
        self.assertListEqual(destinations, expected)


class Type8BinaryMessageTests(unittest.TestCase):
    """
    test being able to distinquish between different types of Type 8 messages
    """

    def test_inland_static_and_voyage_data(self):
        """
        Test to see if a particular type 8 message is recognised
        """
        payload = '83P=pSPj2`8800400PPPM00M5fp0'
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = t8.Type8BinaryBroadcastMessage(msgbinary)
        self.assertEqual(msg.msgsubtype, 'Inland Static & Voyage Data')

    def test_meteorological_and_hydrological_data(self):
        """
        Test to see if a particular type 8 message is recognised
        """
        payload = ('8>jHC700Gwn;21S`2j2ePPFQDB06EuOwgwl'
                   '?wnSwe7wvlO1PsAwwnSAEwvh0')
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = t8.Type8BinaryBroadcastMessage(msgbinary)
        self.assertEqual(msg.msgsubtype,
                         'Meteorological and Hydrological Data')


class Type6BinaryMessageTests(unittest.TestCase):
    """
    test being able to distinquish between different types of Type 6 messages
    """

    def test_navigation_aid_monitoring_UK(self):
        """
        Test to see if a particular type 6 message is recognised
        """
        payload = '6>jHC700V:C0>da6TPAvP00'
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = t6.Type6BinaryMessage(msgbinary)
        self.assertEqual(msg.msgsubtype, 'Aid to Navigation monitoring UK')

    def test_navigation_aid_monitoring_ROI(self):
        """
        Test to see if a particular type 6 message is recognised
        """
        payload = '6>jHC7D0V:C0?``00000P00i'
        msgbinary = binary.ais_sentence_payload_binary(payload)
        msg = t6.Type6BinaryMessage(msgbinary)
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
        self.aistracker.timingsource = ['002320814']
        expected = 'No time data available.'
        timings = [
            '402=acP000HttwhRddNPs;G00l1G',
            '402=acP000HttwhRddNPs;G00p4E',
            '402=acP000HttwhRddNPs;G00t1H',
            '402=acP000HttwhRddNPs;G00UhP']
        for data in timings:
            self.aistracker.process_message(data)
        stats = self.aistracker.tracker_stats()
        self.assertEqual(expected, stats['Times'])

    def test_valid_times_from_base_station(self):
        """
        Tests the aistracker figuring out the start and finish time from
        base station reports that have been received.
        """
        self.aistracker.timingsource = ['002320800']
        expected = {
            "Base Station Timing Reference MMSIs": ["002320800"],
            "Started": "2018/09/09 14:00:36 (estimated)",
            "Finished": "2018/09/09 14:20:06 (estimated)"}
        timings = [
            '402=a`1v:Df0TOi>SHNu0wA020S:',
            '402=a`1v:Df:@Oi>SjNu0si02H9i',
            '402=a`1v:DfBJOi>SRNu0tQ02H?`',
            '402=a`1v:DfD6Oi>SpNu0t102@3r']
        for data in timings:
            self.aistracker.process_message(data)
        stats = self.aistracker.tracker_stats()
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

    def test_str_no_times_no_ships(self):
        """
        get the str for the AIS object on an empty tracker
        there should be no time data
        """
        teststr = ('AIS Tracker - tracking 0 vessels'
                   ' , processed 0 messages, No time data available.')
        actualstr = self.aistracker.__str__()
        self.assertEqual(teststr, actualstr)


class KMLTimingTests(unittest.TestCase):
    """
    test formatting timestamps for KML/KMZ files and other related tests
    """

    def test_suitable_timestamp(self):
        """
        test a valid timestamp in the correct format
        """
        testinput = '2020/06/02 19:03:17'
        expected = '2020-06-02T19:03:17Z'
        teststring = kml.convert_timestamp_to_kmltimestamp(testinput)
        self.assertEqual(expected, teststring)

    def test_suitable_estimated_timestamp(self):
        """
        test a valid timestamp in the correct format
        """
        testinput = '2020/07/03 00:34:17 (estimated)'
        expected = '2020-07-03T00:34:17Z'
        teststring = kml.convert_timestamp_to_kmltimestamp(testinput)
        self.assertEqual(expected, teststring)

    def test_unsuitable_timestamp_regex_fail(self):
        """
        test a timestamp that doesn't match the regex

        Note:
            change this when i come up with a better regex for datetimes
        """
        testinput = '2020-06-02 19:03:17'
        with self.assertRaises(kml.InvalidDateTimeString):
            kml.convert_timestamp_to_kmltimestamp(testinput)

    def test_unsuitable_timestamp_regex_fail_month(self):
        """
        test a timestamp with an invalid month

        Note:
            change this when i come up with a better regex for datetimes
        """
        testinput = '2020/16/06 20:34:09'
        with self.assertRaises(kml.InvalidDateTimeString):
            kml.convert_timestamp_to_kmltimestamp(testinput)

    def test_unsuitable_timestamp_regex_fail_day(self):
        """
        test a timestamp with an invalid day

        Note:
            change this when i come up with a better regex for datetimes
        """
        testinput = '2020/11/62 20:34:09'
        with self.assertRaises(kml.InvalidDateTimeString):
            kml.convert_timestamp_to_kmltimestamp(testinput)

    def test_unsuitable_timestamp_regex_fail_hour(self):
        """
        test a timestamp with an invalid hour

        Note:
            change this when i come up with a better regex for datetimes
        """
        testinput = '2020/11/30 26:34:09'
        with self.assertRaises(kml.InvalidDateTimeString):
            kml.convert_timestamp_to_kmltimestamp(testinput)

    def test_unsuitable_timestamp_regex_fail_minutes(self):
        """
        test a timestamp with an invalid minutes field

        Note:
            change this when i come up with a better regex for datetimes
        """
        testinput = '2020/11/30 17:67:09'
        with self.assertRaises(kml.InvalidDateTimeString):
            kml.convert_timestamp_to_kmltimestamp(testinput)

    def test_unsuitable_timestamp_regex_fail_seconds(self):
        """
        test a timestamp with an invalid seconds field

        Note:
            change this when i come up with a better regex for datetimes
        """
        testinput = '2020/11/30 17:02:78'
        with self.assertRaises(kml.InvalidDateTimeString):
            kml.convert_timestamp_to_kmltimestamp(testinput)


class GeoJSONTests(unittest.TestCase):
    """
    testing the creation of GeoJSON
    """

    def setUp(self):
        self.parser = geojson.GeoJsonParser()
        self.maxDiff = None

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

    def test_json_string(self):
        """
        Tests getting the geojson as a string

        Note:
            we are comparing length as the keys may not be in the same order
        """
        expected = ('{"type": "FeatureCollection", "features": '
                    '[{"type": "Feature", "geometry": {"type": '
                    '"Point", "coordinates": [-3.3356966666666668, '
                    '53.90606666666667]}, "properties": {"MMSI": '
                    '"123456789", "Type": "not specified", "Flag": '
                    '"unknown"}}, {"type": "Feature", "geometry": '
                    '{"type": "LineString", "coordinates": '
                    '[[-4.328763333333334, 53.864983333333335], '
                    '[-3.6327133333333332, 53.90793333333333], '
                    '[-3.3356966666666668, 53.90606666666667]]}, '
                    '"properties": {"MMSI": "123456789"}}]}')
        mmsi = '123456789'
        positions = [
            [-4.328763333333334, 53.864983333333335],
            [-3.6327133333333332, 53.90793333333333],
            [-3.3356966666666668, 53.90606666666667]]
        lon = positions[2][0]
        lat = positions[2][1]
        properties = {'Flag': 'unknown', 'Type': 'not specified', 'MMSI': mmsi}
        self.parser.add_station_info(mmsi, properties, positions, lon, lat)
        geojsonstring = self.parser.get_json_string()
        self.assertEqual(len(expected), len(geojsonstring))


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

    def test_green_arrows(self):
        """
        check that we have the green arrows to represent heading
        """
        exists = 0
        iconspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'static', 'green_arrows')
        for heading in range(0, 360):
            if os.path.exists(os.path.join(iconspath,
                                           str(heading) + '.png')):
                exists += 1
        self.assertEqual(360, exists)

    def test_orange_arrows(self):
        """
        check that we have the orange arrows to represent CoG
        """
        exists = 0
        iconspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'static', 'orange_arrows')
        for heading in range(0, 360):
            if os.path.exists(os.path.join(iconspath,
                                           str(heading) + '.png')):
                exists += 1
        self.assertEqual(360, exists)


class IMONumberTests(unittest.TestCase):
    """
    check IMO integrity check works
    """

    def test_check_valid_imo_number(self):
        """
        a correct IMO number
        """
        self.assertTrue(t5.check_imo_number('9170705'))

    def test_check_invalid_imo_number(self):
        """
        correct length but is not a valid IMO number
        """
        self.assertFalse(t5.check_imo_number('9999999'))

    def test_check_too_short_imo_number(self):
        """
        IMO number that is too short - < 7 chars
        """
        self.assertFalse(t5.check_imo_number('9999'))

    def test_check_too_long_imo_number(self):
        """
        IMO number that is too long - > 7 chars
        """
        self.assertFalse(t5.check_imo_number('917070500005'))


class TextSummaryFormattingTests(unittest.TestCase):
    """
    test the formatting of text summaries that can be printed to screen
    or saved to text file
    """

    def test_text_summary(self):
        """
        feed in a dictionary and see if the str output from the text summary
        method matches our expected output string
        """
        testdict = {
            'AIS Stats': {'Total Unique Stations': 2,
                          'Total Messages Processed': 15,
                          'Message Stats': {
                              'Type 3 - Position Report Class A': 13,
                              'Type 5 - Static and Voyage Related Data': 2},
                          'AIS Station Types': {'Class A': 2},
                          'Ship Types': {'Cargo, all ships of this type': 2},
                          'Country Flags': {'Bahamas': 1, 'Netherlands': 1},
                          'Times': 'No time data available.'},
            'NMEA Stats': {'Total Sentences Processed': 17,
                           'Multipart Messages Reassembled': 2,
                           'Messages Recieved on Channel': {'A': 13, 'B': 4}}}
        expectedstr = r"""
   AIS Stats: 
      Total Unique Stations: 2
      Total Messages Processed: 15
      Message Stats: 
         Type 3 - Position Report Class A: 13
         Type 5 - Static and Voyage Related Data: 2
      
      AIS Station Types: 
         Class A: 2
      
      Ship Types: 
         Cargo all ships of this type: 2
      
      Country Flags: 
         Bahamas: 1
         Netherlands: 1
      
      Times: No time data available.
   
   NMEA Stats: 
      Total Sentences Processed: 17
      Multipart Messages Reassembled: 2
      Messages Recieved on Channel: 
         A: 13
         B: 4
      
   
"""
        testresult = export.create_summary_text(testdict)
        self.assertEqual(testresult, expectedstr)


class TurnRateTests(unittest.TestCase):
    """
    test interpretation of the turn rate field that appears in message types
    1,2 & 3
    """

    def test_no_turn_rate_available(self):
        """
        test value for no turn rate data
        """
        turnrateint = '10000000'
        turnratestr = t123.decode_turn_rate(turnrateint)
        expectedstr = 'no turn rate available'
        self.assertEqual(turnratestr, expectedstr)

    def test_not_turning(self):
        """
        test value for when the vessel is not turning
        """
        turnrateint = '00000000'
        turnratestr = t123.decode_turn_rate(turnrateint)
        expectedstr = 'not turning'
        self.assertEqual(turnratestr, expectedstr)

    def test_right_turn_no_turn_indicator(self):
        """
        test a right turn - test value is 127
        """
        turnrateint = '01111111'
        turnratestr = t123.decode_turn_rate(turnrateint)
        expectedstr = ('turning right at more than 10 degrees per minute'
                       ' - NO TURN INDICATOR')
        self.assertEqual(turnratestr, expectedstr)

    def test_right_turn(self):
        """
        test a right turn of 19.7 degrees per minute
        """
        turnrateint = '00010101'
        turnratestr = t123.decode_turn_rate(turnrateint)
        expectedstr = 'turning right at 19.7 degrees per minute'
        self.assertEqual(turnratestr, expectedstr)

    def test_left_turn_no_turn_indicator(self):
        """
        test a left turn - test value is -127 in twos complement
        (129 as unsigned binary int)
        """
        turnrateint = '10000001'
        turnratestr = t123.decode_turn_rate(turnrateint)
        expectedstr = ('turning left at more than -10 degrees per minute'
                       ' - NO TURN INDICATOR')
        self.assertEqual(turnratestr, expectedstr)

    def test_left_turn(self):
        """
        test a left turn of 12.9 degrees per minute
        """
        turnrateint = '11101111'
        turnratestr = t123.decode_turn_rate(turnrateint)
        expectedstr = 'turning left at -12.9 degrees per minute'
        self.assertEqual(turnratestr, expectedstr)


class MiscTests(unittest.TestCase):
    """
    tests that don't fit into any other catagory
    """

    def test_mmsi_with_single_leading_zero(self):
        """
        identify the flag for MMSI with a single leading zero
        """
        teststn = ais.AISStation('023358500')
        expectedflag = 'United Kingdom'
        self.assertEqual(expectedflag, teststn.flag)


class KMLTests(unittest.TestCase):
    """
    test the generation of Keyhole Markup Language
    """

    def setUp(self):
        self.maxDiff = None
        self.parser = kml.KMLOutputParser(None)

    def test_basic_kml_doc(self):
        """
        create a very basic kml file with a folder containing a point
        """
        testcoords = [
            {'Latitude': 53.81631259853631, 'Longitude': -3.055718449226172},
            {'Latitude': 53.81637571982642, 'Longitude': -3.054978876647683},
            {'Latitude': 53.81553582648765, 'Longitude': -3.054681431837341},
            {'Latitude': 53.81547082550122, 'Longitude': -3.055649507902522},
            {'Latitude': 53.81631259853631, 'Longitude': -3.055718449226172}]
        self.parser.create_kml_header()
        self.parser.open_folder('Blackpool')
        self.parser.add_kml_placemark('Blackpool Tower',
                                      ('Blackpool tower is 158m tall and'
                                       ' was completed in 1894.'),
                                      '-3.055468', '53.815964', '', kmz=False)
        self.parser.add_kml_placemark_linestring('Perimeter', testcoords)
        self.parser.close_folder()
        self.parser.close_kml_file()
        kmldoc = xml.etree.ElementTree.fromstring(''.join(self.parser.kmldoc))
        self.assertIsInstance(kmldoc,
                              xml.etree.ElementTree.Element)

    def test_placemark_html_formatting(self):
        """
        test the formatting of dictionaries into html for the placemarks
        """
        testdict = {
            'mmsi': '992351030', 'type': 'Navigation Aid',
            'subtype': 'Cardinal Mark S', 'name': 'LUNE DEEP BUOY',
            'flag': 'United Kingdom', 'Sent Messages': {
                'Type 21 - Aid to Navigation Report': 15}}
        testhtml = self.parser.format_kml_placemark_description(testdict)
        expectedhtml = """<![CDATA[MMSI - 992351030<br  />
TYPE - Navigation Aid<br  />
SUBTYPE - Cardinal Mark S<br  />
NAME - LUNE DEEP BUOY<br  />
FLAG - United Kingdom<br  />
<br  />
SENT MESSAGES<br  />
TYPE 21 - AID TO NAVIGATION REPORT - 15<br  />
]]>"""
        self.assertEqual(testhtml, expectedhtml)

    def test_kml_invalid_chars(self):
        """
        test removal of invalid characters for KML placemarks
        """
        teststr = '"<hello world>" &\ttest\n'
        clean = kml.remove_invalid_chars(teststr)
        expected = '&quot;&lt;hello world&gt;&quot; &amp;    test'
        self.assertEqual(clean, expected)


if __name__ == '__main__':
    unittest.main()
