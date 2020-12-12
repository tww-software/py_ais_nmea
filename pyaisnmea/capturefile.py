"""
module to deal with getting data from a capture file

nmea capture text files should be plain text files with each NMEA 0183 sentence
on it's own line

jsonlines are files previously exported from pyaisnmea and consist of AIS
message data as seperate JSON statements each on a new line

csv are comma seperated values files exported from pyaisnmea
"""

import json
import logging
import os
import sys

import pyaisnmea.allmessages as allmessages
import pyaisnmea.ais as ais
import pyaisnmea.export as export
import pyaisnmea.binary as binary
import pyaisnmea.kml as kml
import pyaisnmea.nmea as nmea


AISLOGGER = logging.getLogger(__name__)


class NoSuitableMessagesFound(Exception):
    """
    raise if we cannot find any messages in a file
    """


def open_file_generator(filepath):
    """
    open a file line by line using a generator

    Args:
        filepath(str): path to the file

    Yields:
        line(str): a line from the open file
    """
    with open(filepath, 'r') as infile:
        for line in infile:
            if line in ('\n', '\r\n'):
                continue
            yield line


def aistracker_from_csv(filepath, debug=True):
    """
    get an aistracker object from a debug messages CSV that was previously
    exported from pyaisnmea

    Args:
        filepath(str): full path to csv file
        debug(bool): save all message payloads and decoded attributes into
                     messagelog

    Raises:
        NoSuitableMessagesFound: if there are no AIS messages in the file

    Returns:
        aistracker(ais.AISTracker): object that keeps track of all the
                                    ships we have seen
        messagelog(allmessages.AISMessageLog): object with all the AIS messages
    """
    messagelog = allmessages.AISMessageLog()
    aistracker = ais.AISTracker()
    msgnumber = 1
    for line in open_file_generator(filepath):
        try:
            linelist = line.split(',')
            if kml.DATETIMEREGEX.match(linelist[3]):
                payload = linelist[0]
                msgtime = linelist[3]
                msg = aistracker.process_message(payload, timestamp=msgtime)
                if debug:
                    messagelog.store(msgnumber, payload, msg)
                msgnumber += 1
        except (ais.UnknownMessageType, ais.InvalidMMSI,
                IndexError, binary.NoBinaryData) as err:
            AISLOGGER.debug(str(err))
            continue
    if aistracker.messagesprocessed == 0:
        raise NoSuitableMessagesFound('No AIS messages detected in this file')
    return (aistracker, messagelog)


def aistracker_from_json(filepath, debug=True):
    """
    get an aistracker object from a debug messages JSON that was previously
    exported from pyaisnmea

    Args:
        filepath(str): full path to json file
        debug(bool): save all message payloads and decoded attributes into
                     messagelog

    Raises:
        NoSuitableMessagesFound: if there are no AIS messages in the file

    Returns:
        aistracker(ais.AISTracker): object that keeps track of all the
                                    ships we have seen
        messagelog(allmessages.AISMessageLog): object with all the AIS messages
    """
    messagelog = allmessages.AISMessageLog()
    aistracker = ais.AISTracker()
    msgnumber = 1
    for line in open_file_generator(filepath):
        try:
            linemsgdict = json.loads(line)
            payload = linemsgdict['payload']
            msgtime = linemsgdict['rxtime']
            msg = aistracker.process_message(payload, timestamp=msgtime)
            if debug:
                messagelog.store(msgnumber, payload, msg)
            msgnumber += 1
        except (ais.UnknownMessageType, ais.InvalidMMSI,
                json.decoder.JSONDecodeError, KeyError,
                binary.NoBinaryData) as err:
            AISLOGGER.debug(str(err))
            continue
    if aistracker.messagesprocessed == 0:
        raise NoSuitableMessagesFound('No AIS messages detected in this file')
    return (aistracker, messagelog)


def aistracker_from_file(filepath, debug=False, timingsource=None):
    """
    open a file, read all nmea sentences and return an ais.AISTracker object

    Note:
        if debug is set then individual messages are saved into the messagelog

    Args:
        filepath(str): full path to nmea file
        debug(bool): save all message payloads and decoded attributes into
                     messagelog
        timingsource(list): MMSIs of the base stations you wish to use
                           as a time reference, type 4 base station reports
                           from this base station will be used for times.
                           default is None and all base stations will be used
                           for times. list of strings

    Raises:
        NoSuitableMessagesFound: if there are no AIS messages in the file

    Returns:
        aistracker(ais.AISTracker): object that keeps track of all the
                                    ships we have seen
        nmeatracker(nmea.NMEAtracker): object that organises the nmea sentences
        messagelog(allmessages.AISMessageLog): object with all the AIS messages
    """
    messagelog = allmessages.AISMessageLog()
    aistracker = ais.AISTracker()
    aistracker.timingsource = timingsource
    nmeatracker = nmea.NMEAtracker()
    msgnumber = 1
    for line in open_file_generator(filepath):
        try:
            payload = nmeatracker.process_sentence(line)
            if payload:
                msg = aistracker.process_message(payload)
                if debug:
                    messagelog.store(msgnumber, payload, msg)
                msgnumber += 1
        except (nmea.NMEAInvalidSentence, nmea.NMEACheckSumFailed,
                ais.UnknownMessageType, ais.InvalidMMSI,
                binary.NoBinaryData, IndexError) as err:
            AISLOGGER.debug(str(err))
            continue
    if aistracker.messagesprocessed == 0:
        raise NoSuitableMessagesFound('No AIS messages detected in this file')
    return (aistracker, nmeatracker, messagelog)


def extract_time_data_from_file(filepath):
    """
    find the base stations and timing data from NMEA text files

    Args:
        filepath(str): path to the nmea0183 text file

    Returns:
        timingchoices(dict): keys are numbers, values are MMSIs of base stns
        basestntable(list): list of lists, each list is a row for an AIS
                            base stn with its MMSI, flag, total messages, first
                            and last known timestamps

    Raises:
        NoSuitableMessagesFound: if there are no type 4 messages in the file
                                 there is no usable timestamps
    """
    nmeatracker = nmea.NMEAtracker()
    basestntracker = ais.BaseStationTracker()
    for line in open_file_generator(filepath):
        try:
            payload = nmeatracker.process_sentence(line)
            if payload:
                basestntracker.process_message(payload)
        except (nmea.NMEAInvalidSentence, nmea.NMEACheckSumFailed,
                ais.UnknownMessageType, ais.InvalidMMSI,
                binary.NoBinaryData, IndexError) as err:
            AISLOGGER.debug(str(err))
            continue
    if basestntracker.messagesprocessed == 0:
        raise NoSuitableMessagesFound('No AIS Base Stations detected')
    basestnmainheader = ['MMSI', 'Flag', 'Total Messages',
                         'First Known Time', 'Last Known Time']
    basestnposheader = ['Time']
    basestntable = basestntracker.create_table_data(
        csvheader=basestnmainheader, posheaders=basestnposheader)
    basestntable[0].insert(0, 'Choice')
    timingchoices = {}
    stncount = 1
    for stn in basestntracker.stations:
        timingchoices[str(stncount)] = stn
        basestntable[stncount].insert(0, stncount)
        stncount += 1
    return timingchoices, basestntable


def print_table(tablelist):
    """
    neatly print a table to the terminal

    Note: finds out the maximun length of each column then adds whitespace
          padding to each of the fields

    Args:
        tablelist(list): a list of lists each list is a row on the table

    Returns:
        tablelist(list): input but with padding so all entries are the same
                         width as the widest entry
    """
    columnlengths = [0 for x in tablelist[0]]
    for row in tablelist:
        colno = 0
        for column in row:
            columnlength = len(str(column))
            if columnlength > columnlengths[colno]:
                columnlengths[colno] = columnlength
            colno += 1
    for row in tablelist:
        colno = 0
        for column in row:
            columnlength = len(str(column))
            padding = columnlengths[row.index(column)] - columnlength
            row[row.index(column)] = str(column) + ' ' * padding
    for line in tablelist:
        print('  '.join([str(x) for x in line]))
    return tablelist


def read_from_file(
        filepath, outpath, everything=False, filetype='text', orderby='Types',
        region='A'):
    """
    read AIS NMEA sentences from a text file and save to various output formats

    Note:
        a text file containing stats and a basic summary, a KMZ map,
        JSON + CSV containing details of AIS stations and JSONLINES + CSV of
        all AIS messages are generated by default

    Args:
        filepath(str): full path to the input file containing NMEA sentences
        outpath(str): path to save to excluding file extensions
        everything(bool): whether to output files for every individual station
        filetype(str): what type of file are we reading from
                       options are text, csv or jsonlines
        orderby(str): order KML/KMZ output and Everything station folders by
                      'Types', 'Flags' or 'Class', default is 'Types'
        region(str): IALA region 'A' or 'B', default is 'A'
    """
    if not os.path.exists(outpath):
        AISLOGGER.info('output path does not exist creating directories')
        os.makedirs(outpath)
    AISLOGGER.info('processed output will be saved in %s', outpath)
    AISLOGGER.info('reading nmea sentences from - %s', filepath)
    timesources = []
    try:
        if filetype == 'text':
            try:
                AISLOGGER.info('importing as text file')
                basestnchoices, basestntable = extract_time_data_from_file(
                    filepath)
                AISLOGGER.info('choose timing source')
                choiceconfirmed = False
                while not choiceconfirmed:
                    print_table(basestntable)
                    choice = input('enter timing source choice number: ')
                    try:
                        basestnmmsi = basestnchoices[choice.rstrip()]
                        if basestnmmsi not in timesources:
                            timesources.append(basestnmmsi)
                    except KeyError:
                        AISLOGGER.error('enter a choice no!')
                        continue
                    AISLOGGER.info('use %s as a time reference',
                                   basestnmmsi)
                    yesno = input('Y/N: ')
                    if yesno.rstrip() in ('Y', 'y', 'yes', 'YES'):
                        AISLOGGER.info(
                            'timing sources to be used - %s', timesources)
                        yesno2 = input('add another timing source? Y/N: ')
                        if yesno2.rstrip() in ('N', 'n', 'no', 'NO'):
                            basestntimingsource = timesources
                            choiceconfirmed = True
            except NoSuitableMessagesFound as err:
                basestntimingsource = None
                AISLOGGER.error(str(err))
            aistracker, nmeatracker, messagelog = aistracker_from_file(
                filepath, debug=True, timingsource=basestntimingsource)
        elif filetype == 'csv':
            AISLOGGER.info('importing as CSV file')
            aistracker, messagelog = aistracker_from_csv(
                filepath, debug=True)
        elif filetype == 'jsonlines':
            AISLOGGER.info('importing as JSON lines file')
            aistracker, messagelog = aistracker_from_json(
                filepath, debug=True)
        if filetype in ('csv', 'jsonlines'):
            nmeatracker = nmea.NMEAtracker()
            nmeatracker.sentencecount = 'N/A'
            nmeatracker.reassembled = 'N/A'
    except (FileNotFoundError, NoSuitableMessagesFound) as err:
        AISLOGGER.info(str(err))
        sys.exit(1)
    export.export_overview(
        aistracker, nmeatracker, messagelog, outpath, printsummary=True,
        orderby=orderby, region=region)
    if everything:
        export.export_everything(
            aistracker, messagelog, outpath, orderby=orderby, region=region)
    AISLOGGER.info('Finished')
