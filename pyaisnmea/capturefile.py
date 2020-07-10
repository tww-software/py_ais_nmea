"""
module to deal with getting data from a capture file

capture files should be plain text files with each NMEA 0183 sentence
on it's own line
"""

import json
import logging
import os
import sys

import pyaisnmea.allmessages as allmessages
import pyaisnmea.ais as ais
import pyaisnmea.binary as binary
import pyaisnmea.kml as kml
import pyaisnmea.nmea as nmea


AISLOGGER = logging.getLogger(__name__)


class NoSuitableMessagesFound(Exception):
    """
    raise if we cannot find any messages in a file
    """
    pass


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
            if line == '\n' or line == '\r\n':
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


def aistracker_from_file(filepath, debug=False):
    """
    open a file, read all nmea sentences and return an ais.AISTracker object

    Note:
        if debug is set then individual messages are saved into the messagelog

    Args:
        filepath(str): full path to nmea file
        debug(bool): save all message payloads and decoded attributes into
                     messagelog

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


def read_from_file(filepath, outpath, debug=False,
                   jsonoutput=True, geojsonoutput=True, csvoutput=True,
                   tsvoutput=False,
                   kmloutput=False, kmzoutput=True, verbosejson=False):
    """
    read AIS NMEA sentences from a text file and save to various output formats

    Note:
        a text file containing stats and a basic summary
        is generated by default

    Args:
        filepath(str): full path to the input file containing NMEA sentences
        outpath(str): path to save to excluding file extensions
        debug(bool): create a json lines file and a csv file containing
                     all the individual messages
                     decoded with the original payloads
        jsonoutput(bool): save output to json file
        geojsonoutput(bool): save output to geojson file
        csvoutput(bool): save output to csv file
        kmloutput(bool): save output to kml file
        kmzoutput(bool): save output to kmz file
    """
    if not os.path.exists(outpath):
        AISLOGGER.info('output path does not exist creating directories')
        os.makedirs(outpath)
    AISLOGGER.info('processed output will be saved in %s', outpath)
    AISLOGGER.info('reading nmea sentences from - %s', filepath)
    try:
        aistracker, nmeatracker, messagelog = aistracker_from_file(
            filepath, debug=debug)
    except (FileNotFoundError, NoSuitableMessagesFound) as err:
        AISLOGGER.info(str(err))
        sys.exit(1)
    stnstats = aistracker.tracker_stats()
    sentencestats = nmeatracker.nmea_stats()
    AISLOGGER.debug('saving summary to summary.txt')
    summary = ais.create_summary_text({'AIS Stats': stnstats,
                                       'NMEA Stats': sentencestats,
                                       'Capture File': filepath})
    with open(os.path.join(outpath, 'summary.txt'), 'w') as textsummary:
        textsummary.write(summary)
    print(summary)
    if jsonoutput:
        joutdict = {}
        joutdict['NMEA Stats'] = sentencestats
        joutdict['AIS Stats'] = stnstats
        joutdict['AIS Stations'] = aistracker.all_station_info(
            verbose=verbosejson)
        ais.write_json_file(joutdict,
                            os.path.join(outpath, 'vessel-data.json'))
    if geojsonoutput:
        aistracker.create_geojson_map(os.path.join(outpath, 'map.geojson'))
    if csvoutput or tsvoutput:
        outputdata = aistracker.create_table_data()
        if csvoutput:
            ais.write_csv_file(outputdata,
                               os.path.join(outpath, 'vessel-data.csv'))
        if tsvoutput:
            ais.write_csv_file(outputdata,
                               os.path.join(outpath, 'vessel-data.tsv'),
                               dialect='excel-tab')
    if kmloutput:
        aistracker.create_kml_map(os.path.join(outpath, 'map.kml'),
                                  kmzoutput=False)
    if kmzoutput:
        aistracker.create_kml_map(os.path.join(outpath, 'map.kmz'),
                                  kmzoutput=True)
    if debug:
        jsonlineslist, messagecsvlist = messagelog.debug_output()
        ais.write_json_lines(jsonlineslist,
                             os.path.join(outpath,
                                          'ais-messages.jsonl'))
        ais.write_csv_file(messagecsvlist,
                           os.path.join(outpath, 'ais-messages.csv'))
    AISLOGGER.info('Finished')
