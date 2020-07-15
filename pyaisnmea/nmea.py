"""
module to parse nmea 0183 sentences
"""


import collections
import re


NMEASENTENCEREGEX = re.compile(
    r'!AIVD[MO],\d,\d,\d?,[AB12],[A-Za-z0-9`:;<=>?@]{1,56},'
    r'[0-5][*][0-9A-F]{2}')


def calculate_nmea_checksum(sentence, start='!', seperator=','):
    """
    XOR each char with the last, compare the last 2 characters
    with the computed checksum

    Args:
        sentence(str): the ais sentence as a string
        start(str): the start of the sentence default = !
        separator(str): character that separates the parts of the nmea sentence
                        default = ,

    Returns:
        True: if calculated checksum = checksum at the end of the sentence
        False: if checksums do not match
    """
    sentencelist = sentence.rstrip().split(seperator)
    csum = hex(int(sentencelist[len(sentencelist) - 1].split('*')[1], 16))
    start = sentence.find(start) + 1
    end = sentence.find('*')
    data = sentence[start:end]
    chksum = 0
    for char in data:
        chksum ^= ord(char)
    chksum = hex(int(chksum))
    return bool(csum == chksum)


class NMEAInvalidSentence(Exception):
    """
    raise when the nmea sentence isn't valid
    """
    pass


class NMEACheckSumFailed(Exception):
    """
    raise when the nmea checksum doesn't match the calculated value
    """
    pass


class NMEA0183Sentence():
    """
    class to parse a single NMEA 0183 sentence

    Args:
        sentence(str): the nmea sentence as a string
        errorcheck(bool): if set to true, the checksum will be calculated to
                          ensure the sentence is correctly formed
                          default is True

    Attributes:
        sentencestr(str) the input sentence as a string
                         same as sentence in args
        type(str): the nmea sentence type
        fragmentcount(int): number of sentences the message consists of
        fragmentno(int): the fragment no for this part of the message
        msgsequenceid(str): id that identifies the whole message
        channel(str): the AIS channel that this sentence was recieved on
        data(str): the data payload of the sentence
        checksum(str): the checksum of the sentence
    """

    def __init__(self, sentence, errorcheck=True):
        self.sentencestr = sentence
        if not NMEASENTENCEREGEX.match(sentence):
            raise NMEAInvalidSentence('NMEA 0183 sentence regex'
                                      ' check failed - ' + sentence)
        sentencelist = sentence.split(',')
        self.type = sentencelist[0]
        self.fragmentcount = int(sentencelist[1])
        self.fragmentno = int(sentencelist[2])
        self.msgsequenceid = sentencelist[3]
        self.channel = sentencelist[4]
        self.data = sentencelist[5]
        self.checksum = sentencelist[6].split('*')[1]
        if errorcheck:
            self.check_sentence_is_valid()

    def check_sentence_is_valid(self):
        """
        check that the sentence is valid

        Raises:
            NMEACheckSumFailed: raised if the checksum in the sentence and the
                                checksum calculated by calculate_nmea_checksum
                                doesn't match

        Returns:
            True: if no errors are detected
        """
        if calculate_nmea_checksum(self.sentencestr):
            return True
        else:
            raise NMEACheckSumFailed('checksum calculated does not match ' +
                                     self.checksum)


class NMEAtracker():
    """
    class to process NMEA sentences and track multipart sentences

    Attributes:
        multiparts(dict): dictionary to track ais messages spread over multiple
                          sentences
        sentencecount(int): the number of sentences that have been processed
        reassembled(int): the number of multipart messages that have been
                          assembled
        channelcounter(collections.Counter): count sentences recieved on each
                                             channel
    """

    def __init__(self):
        self.multiparts = collections.defaultdict(dict)
        self.sentencecount = 0
        self.reassembled = 0
        self.channelcounter = collections.Counter()

    def __str__(self):
        strtext = ('NMEA 0183 sentence Tracker - {} sentences processed,'
                   ' {} multipart messages '
                   'reassembled, messages recieved on {}').format(
                       self.sentencecount,
                       self.reassembled,
                       str(dict(self.channelcounter)))
        return strtext

    def __repr__(self):
        reprstr = '{}()'.format(self.__class__.__name__)
        return reprstr

    def nmea_stats(self):
        """
        return stats calculated from the sentences we have processed

        Returns:
            stats(dict): dictionary of stats for the NMEA sentences
        """
        stats = {}
        stats['Total Sentences Processed'] = self.sentencecount
        stats['Multipart Messages Reassembled'] = self.reassembled
        stats['Messages Recieved on Channel'] = dict(self.channelcounter)
        return stats

    def process_sentence(self, sentence):
        """
        takes a nmea sentence creates a NMEA0183Sentence object
        determines if it is part of a multipart message, if a single message
        returns the NMEA0183Sentence objects data, if the sentence contains
        part of a larger message then it is stored in the multiparts dict until
        all parts are recieved.

        Args:
            sentence(str): the nmea sentence as a string

        Returns:
            newsen.data(str): the data payload of the sentence as a string
                              this is returned if its a 1 part message
            completemessage(str): the data payload of several sentences joined
                                  together as a string
            multiparts[newsen.msgsequenceid][1](str): returned if failed to
                                                      reassemble a multipart
                                                      message
            None: returned if no sentence data to process
        """
        newsen = NMEA0183Sentence(sentence)
        self.channelcounter[newsen.channel] += 1
        self.sentencecount += 1
        if newsen.fragmentno == 1 and newsen.fragmentcount == 1:
            return newsen.data
        self.multiparts[newsen.msgsequenceid][newsen.fragmentno] = newsen.data
        msglength = len(self.multiparts[newsen.msgsequenceid].keys())
        if msglength == newsen.fragmentcount:
            msg = []
            for i in range(1, msglength + 1):
                try:
                    msg.append(self.multiparts[newsen.msgsequenceid][i])
                except KeyError:
                    print('missing part of message, returning 1st part')
                    return self.multiparts[newsen.msgsequenceid][1]
            completemessage = ''.join(msg)
            self.reassembled += 1
            del self.multiparts[newsen.msgsequenceid]
            return completemessage
