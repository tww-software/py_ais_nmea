"""
helper module to get all the AIS messages together in one module
"""

# pylint: disable=no-member
# pylint: disable=import-error
# pylint: disable=no-name-in-module

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

MSGDESCRIPTIONS = messages.aismessage.MSGDESCRIPTIONS

MSGTYPES = {
    0: messages.aismessage.AISMessage,
    1: messages.t123.Type123PositionReportClassA,
    2: messages.t123.Type123PositionReportClassA,
    3: messages.t123.Type123PositionReportClassA,
    4: messages.t4.Type4BaseStationReport,
    5: messages.t5.Type5StaticAndVoyageData,
    6: messages.t6.Type6BinaryMessage,
    7: messages.t7.Type7BinaryAcknowlegement,
    8: messages.t8.Type8BinaryBroadcastMessage,
    9: messages.t9.Type9StandardSARAircraftPositionReport,
    10: messages.t10.Type10UTCDateInquiry,
    11: messages.t11.Type11UTCDateResponse,
    12: messages.t12.Type12AddressedSafetyMessage,
    13: messages.t13.Type13SafetyAcknowlegement,
    14: messages.t14.Type14SafetyBroadcastMessage,
    15: messages.t15.Type15Interrogation,
    16: messages.t16.Type16AssignmentModeCommand,
    17: messages.t17.Type17DGNSSBroadcastBinaryMessage,
    18: messages.t18.Type18PositionReportClassB,
    19: messages.t19.Type19ExtendedReportClassB,
    20: messages.t20.Type20DatalinkManagementMessage,
    21: messages.t21.Type21AidToNavigation,
    22: messages.t22.Type22ChannelManagement,
    23: messages.t23.Type23GroupAssignmentCommand,
    24: messages.t24.Type24StaticDataReport,
    25: messages.t25.Type25SingleSlotBinaryMessage,
    26: messages.t26.Type26MultipleSlotBinaryMessage,
    27: messages.t27.Type27LongRangeAISPositionReport}
