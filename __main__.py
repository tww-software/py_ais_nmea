"""
command line interface for processing AIS traffic
"""

import argparse
import datetime
import logging
import os
import socket
import subprocess

import ais
import allmessages
import binary
import nmea


AISLOGGER = logging.getLogger(__name__)


def cli_arg_parser():
    """
    get the cli arguments and run the program

    Returns:
        args(argparse.Namespace): the command line options
    """
    desc = 'tool to decode AIS traffic and generate meaningful data'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-v', action='store_true', help='verbose output')
    subparsers = parser.add_subparsers(dest='subcommand')
    netparser = subparsers.add_parser('net',
                                      help=('read AIS traffic from a '
                                            'UDP network port'))
    netparser.add_argument(help='output file path', dest='outputfile')
    fileparser = subparsers.add_parser('file',
                                       help=('read AIS traffic '
                                             'from a capture file'))
    fileparser.add_argument(help='input file path', dest='inputfile')
    fileparser.add_argument(help='output file path', dest='outputfile')
    outputformats = fileparser.add_argument_group('output formats')
    outputformats.add_argument('-j', action='store_true', help='json output')
    outputformats.add_argument('-g', action='store_true',
                               help='geojson output')
    outputformats.add_argument('--kmz', action='store_true', help='kmz output')
    outputformats.add_argument('--kml', action='store_true', help='kml output')
    outputformats.add_argument('-c', action='store_true', help='csv output')
    outputformats.add_argument('-d', action='store_true',
        help=('read AIS traffic from a capture file then decode'
              ' and display all the messages individually'))
    args = parser.parse_args()
    return args


def read_from_network(outpath, host='localhost', port=10110):
    """
    read from network traffic

    Args:
        outpath(str): path to save nmea sentences to
        host(str): hostname to listen on default is localhost
        port(int): UDP port to listen on default is 10110
    """
    AISLOGGER.info('reading nmea sentences from network')
    aistracker = ais.AISTracker()
    nmeatracker = nmea.NMEAtracker()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    with open(outpath, 'w') as fout:
        while True:
            data, _ = sock.recvfrom(1024)
            try:
                ascii = data.decode('ascii')
                payload = nmeatracker.process_sentence(ascii)
                if payload:
                    fout.write(ascii)
                    nowts = datetime.datetime.utcnow()
                    msg = aistracker.process_message(payload, nowts)
                    #subprocess.run('clear')
                    #aistracker.print_table()
                    print(msg.__str__())
            except nmea.NMEAInvalidSentence as err:
                AISLOGGER.debug(str(err))
                continue
            except nmea.NMEACheckSumFailed as err:
                AISLOGGER.debug(str(err))
                continue
            except ais.UnknownMessageType as err:
                AISLOGGER.debug(str(err))
                AISLOGGER.debug('unknown message - %s', data)
                continue
            except ais.InvalidMMSI as err:
                AISLOGGER.debug(str(err))
                continue
            except IndexError:
                AISLOGGER.debug('no data on line')
                continue
            except KeyboardInterrupt:
                AISLOGGER.info('user exited')
                break


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


def read_from_file(filepath, outpath, debug=False,
                   jsonoutput=True, geojsonoutput=True, csvoutput=True,
                   kmloutput=False, kmzoutput=True):
    """
    read AIS NMEA sentences from a text file and save to various output formats

    Note:
        a text file containing stats and a basic summary
        is generated by default

    Args:
        filepath(str): full path to the input file containing NMEA sentences
        outpath(str): path to save to excluding file extensions
        debug(bool): create a csv file containing all the individual messages
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
    headers = ['Message Payload', 'Message Type Number', 'MMSI',
               'Message Description']
    messagelist = []
    messagelist.append(headers)
    aistracker = ais.AISTracker()
    nmeatracker = nmea.NMEAtracker()
    for line in open_file_generator(filepath):
        try:
            payload = nmeatracker.process_sentence(line)
            if payload:
                msg = aistracker.process_message(payload)
                if debug:
                    msglist = []
                    msglist.append(payload)
                    msglist.append(msg.msgtype)
                    msglist.append(msg.mmsi)
                    msglist.append(msg.__str__())
                    messagelist.append(msglist)
        except (nmea.NMEAInvalidSentence, nmea.NMEACheckSumFailed,
                ais.UnknownMessageType, ais.InvalidMMSI) as err:
            AISLOGGER.debug(str(err))
            continue
        except IndexError:
            AISLOGGER.debug('no data on line')
            continue
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
        joutdict['AIS Stations'] = aistracker.all_station_info()
        ais.write_json_file(joutdict, os.path.join(outpath, 'vessel-data.json'))
    if geojsonoutput:
        aistracker.create_geojson_map(os.path.join(outpath, 'map.geojson'))
    if csvoutput:
        csvdata = aistracker.create_csv_data()
        ais.write_csv_file(csvdata, os.path.join(outpath, 'vessel-data.csv'))
    if kmloutput:
        aistracker.create_kml_map(os.path.join(outpath, 'map.kml'), kmzoutput=False)
    if kmzoutput:
        aistracker.create_kml_map(os.path.join(outpath, 'map.kmz'), kmzoutput=True)
    if debug:
        ais.write_csv_file(messagelist, os.path.join(outpath, 'ais-messages.csv'))
    AISLOGGER.info('Finished')


def main():
    CLIARGS = cli_arg_parser()
    if CLIARGS.v:
        logging.basicConfig(level=logging.DEBUG,
                            handlers=[logging.StreamHandler()])
        logging.debug('verbose logging selected')
    else:
        logging.basicConfig(level=logging.INFO,
                            handlers=[logging.StreamHandler()])
    if CLIARGS.subcommand == 'file':
        read_from_file(CLIARGS.inputfile, CLIARGS.outputfile, CLIARGS.d,
                       jsonoutput=CLIARGS.j,
                       geojsonoutput=CLIARGS.g, csvoutput=CLIARGS.c,
                       kmloutput=CLIARGS.kml, kmzoutput=CLIARGS.kmz)
    elif CLIARGS.subcommand == 'net':
        read_from_network(CLIARGS.outputfile)
    else:
        CLIARGS.print_help()

if __name__ == '__main__':
    main()
