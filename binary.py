"""
binary operations for AIS messages
"""


import re


SIXBIT = {0: '@', 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G',
          8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'O',
          16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V',
          23: 'W', 24: 'X', 25: 'Y', 26: 'Z', 27: '[', 28: '\\', 29: ']',
          30: '^', 31: '_', 32: ' ', 33: '!', 34: '"', 35: '#', 36: '$',
          37: '%', 38: '&', 39: '\'', 40: '(', 41: ')', 42: '*', 43: '+',
          44: ',', 45: '-', 46: '.', 47: '/', 48: '0', 49: '1', 50: '2',
          51: '3', 52: '4', 53: '5', 54: '6', 55: '7', 56: '8', 57: '9',
          58: ':', 59: ';', 60: '<', 61: '=', 62: '>', 63: '?'}


SIXBITREGEX = re.compile('[01]{6}')


def ais_sentence_payload_binary(payload):
    """
    Take the payload from a AIS NMEA sentence and convert
    it into a binary string

    Args:
        payload(str): the payload from a AIS NMEA sentence

    Returns:
        binarystr(str): the payload represented as binary
                        in a string e.g '01101010111'
    """
    decoded = []
    for char in payload:
        sixbitchar = ord(char) - 48
        if sixbitchar > 40:
            sixbitchar = sixbitchar - 8
        decoded.append(f'{sixbitchar:06b}')
    binarystr = ''.join(decoded)
    return binarystr


def ais_sentence_binary_payload(binarystr):
    """
    take a binary string and convert it into a NMEA 0183 payload

    Args:
        binarystr(str): the payload represented as binary
                        in a string e.g '01101010111'

    Returns:
        payload(str): the payload from a AIS NMEA sentence

    """
    encoded = []
    bitslist = SIXBITREGEX.findall(binarystr)
    for part in bitslist:
        integer = int(part, 2)
        if integer > 40:
            integer = integer + 8
        char = chr(integer + 48)
        encoded.append(char)
    payload = ''.join(encoded)
    return payload


def decode_sixbit_integer(binary, start, stop):
    """
    used to decode parts of the data that are meant
    to be represented as integers

    Args:
        binary(str): binary as a string

    Returns:
        decodedint(int): the decoded int
        0(int): if an empty string is entered
    """
    if binary[start:stop] == '':
        #maybe raise a exception here instead of returning 0
        return 0
    decodedint = int(binary[start:stop], 2)
    return decodedint


def decode_sixbit_ascii(binary, start, stop):
    """
    used to decode parts of the data that are meant to be represented as text
    this function takes binary as a string splits it into groups of
    6 binary digits
    converts to an integer and looks up the corresponding char
    in the SIXBIT dictionary
    the resulting string is returned.

    Note:
        AIS padds out fields with @ characters,
        these are stripped from the end of the string

    Args:
         binary(str): binary as a string e.g ''.join(decoded)
         start(int): the position to start extracting data from
         stop(int): the postion to stop extracting (up to and not including)

    Returns:
         decodedstr(str): the decoded data as a string
    """
    part = binary[start:stop]
    bitslist = SIXBITREGEX.findall(part)
    charlist = []
    for bit in bitslist:
        char = SIXBIT[int(bit, 2)]
        charlist.append(char)
    decodedstr = ''.join(charlist).rstrip('@')
    return decodedstr


def decode_twos_complement(binary):
    """
    used to decode the binary that is represented as twos complement

    Note:
        flip the bits and add one!

    Args:
        binary(str): the binary as a string

    Returns:
        twoscomplement(int): the number as an integer
    """
    if binary[0] == '1':
        newbinlist = []
        for i in binary:
            if i == '0':
                newbinlist.append('1')
            elif i == '1':
                newbinlist.append('0')
        onescomplement = ''.join(newbinlist)
        twoscomplement = -int(onescomplement, 2) + 1
    else:
        twoscomplement = int(binary, 2)
    return twoscomplement
