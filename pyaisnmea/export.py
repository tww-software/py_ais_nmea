"""
code for the export of data into various file formats
"""

import csv
import json
import logging
import os
import re


AISLOGGER = logging.getLogger(__name__)

INVALIDDIRCHARSREGEX = re.compile(r'[/\*><:|?"]')


def write_json_file(jsonstations, outpath):
    """
    write jsonstations to a json file

    Args:
        jsonstations(dict): data to be written to json file
        outpath(str): full path to write to
    """
    with open(outpath, 'w') as jsonfile:
        json.dump(jsonstations, jsonfile, indent=2)


def write_json_lines(datalist, outpath):
    """
    take a list of dictionaries and write them out to a JSON lines file

    Note:
        JSON lines is a text file where each new line is a separate JSON string

    Args:
        datalist(list): a list of dictionaries to write out
        outpath(str): the full filepath to write to
    """
    with open(outpath, 'w') as jsonlines:
        for jdict in datalist:
            jsonlines.write(json.dumps(jdict) + '\n')


def write_csv_file(lines, outpath, dialect='excel'):
    """
    write out the details to a csv file

    Note:
        default dialect is 'excel' to create a CSV file
        we change this to 'excel-tab' for TSV output

    Args:
        lines(list): list of lines to write out to the csv, each line is a list
        outpath(str): full path to write the csv file to
        dialect(str): type of seperated values file we are creating
    """
    with open(outpath, 'w') as outfile:
        csvwriter = csv.writer(outfile, dialect=dialect)
        csvwriter.writerows(lines)


def create_summary_text(summary):
    """
    format a dictionary so it can be printed to screen or written to a plain
    text file

    Args:
        summary(dict): the data to format

    Returns:
        textsummary(str): the summary dict formatted as a string
    """
    summaryjson = json.dumps(summary, indent=3)
    textsummary = re.sub('[{},"]', '', summaryjson)
    return textsummary


def export_overview(
        aistracker, nmeatracker, aismsglog, outputdir, printsummary=False,
        orderby='Types'):
    """
    export the most popular file formats
    KMZ - map
    JSON & CSV - vessel details
    JSONLINES and CSV - AIS message debug - ALL AIS MESSAGES

    Args:
        aistracker(ais.AISTracker): object tracking all AIS stations
        nmeatracker(nmea.NMEAtracker): object to process NMEA sentences
        aismsglog(allmessages.AISMessageLog): object to log all AIS messages
        outputdir(str): directory path to export files to
        printsummary(bool): whether to print a summary to the terminal
        orderby(str): order the stations by 'Types', 'Flags' or 'Class'
                          default is 'Types'
    """
    stnstats = aistracker.tracker_stats()
    sentencestats = nmeatracker.nmea_stats()
    summary = create_summary_text({'AIS Stats': stnstats,
                                   'NMEA Stats': sentencestats})
    with open(os.path.join(outputdir, 'summary.txt'), 'w') as textsummary:
        textsummary.write(summary)
    if printsummary:
        print(summary)
    joutdict = {}
    joutdict['NMEA Stats'] = sentencestats
    joutdict['AIS Stats'] = stnstats
    joutdict['AIS Stations'] = aistracker.all_station_info(
        verbose=False)
    write_json_file(
        joutdict, os.path.join(outputdir, 'vessel-data.json'))
    outputdata = aistracker.create_table_data()
    write_csv_file(
        outputdata, os.path.join(outputdir, 'vessel-data.csv'))
    aistracker.create_kml_map(
        os.path.join(outputdir, 'map.kmz'), kmzoutput=True, orderby=orderby)
    jsonlineslist, messagecsvlist = aismsglog.debug_output()
    write_json_lines(
        jsonlineslist, os.path.join(outputdir, 'ais-messages.jsonl'))
    write_csv_file(
        messagecsvlist, os.path.join(outputdir, 'ais-messages.csv'))


def export_everything(aistracker, aismsglog, outputdir, orderby='Types'):
    """
    export everything we have on each AIS Station

    Args:
        aistracker(ais.AISTracker): object tracking all AIS stations
        aismsglog(allmessages.AISMessageLog): object to log all AIS messages
        outputdir(str): directory path to export files to
        orderby(str): order the stations by 'Types', 'Flags' or 'Class'
                          default is 'Types'
    """
    AISLOGGER.info('outputting data for all AIS stations')
    mmsicatagories = aistracker.sort_mmsi_by_catagory()
    aisstndir = os.path.join(outputdir, 'AIS Stations')
    try:
        os.mkdir(aisstndir)
    except FileExistsError:
        pass
    for catagory in mmsicatagories[orderby]:
        AISLOGGER.info('processing %s', catagory)
        try:
            os.mkdir(os.path.join(aisstndir, catagory))
        except FileExistsError:
            pass
        for mmsi in mmsicatagories[orderby][catagory]:
            stnobj = aistracker.stations[mmsi]
            if stnobj.name != '':
                foldername = '{} - {}'.format(
                    mmsi, INVALIDDIRCHARSREGEX.sub('', stnobj.name))
            else:
                foldername = mmsi
            AISLOGGER.info('    processing %s', foldername)
            mmsipath = os.path.join(aisstndir, catagory, foldername)
            try:
                os.mkdir(mmsipath)
            except FileExistsError:
                pass
            stnobj.create_kml_map(
                os.path.join(mmsipath, 'map.kmz'), kmzoutput=True)
            stninfo = stnobj.get_station_info(verbose=True, messagetally=True)
            write_json_file(
                stninfo, os.path.join(mmsipath, 'vessel-data.json'))
            stnobj.create_positions_csv(
                os.path.join(mmsipath, 'vessel-positions.csv'))
            msgsjsonlines, msgscsv = aismsglog.debug_output(mmsi=mmsi)
            write_json_lines(msgsjsonlines,
                             os.path.join(mmsipath, 'ais-messages.jsonl'))
            write_csv_file(msgscsv, os.path.join(mmsipath, 'ais-messages.csv'))
