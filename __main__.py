"""
command line interface for processing AIS traffic
"""

import argparse
import datetime
import logging
import pprint
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
    fileparser.add_argument('-o', help='output file path', dest='outputfile')
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
    """
    with open(filepath, 'r') as infile:
        for line in infile:
            if line == '\n' or line == '\r\n':
                continue
            yield line


def read_from_file(filepath, outpath, debug=False, jsonverbose=False,
                   jsonoutput=True, geojsonoutput=True, csvoutput=True,
                   kmloutput=False, kmzoutput=True):
    """
    read AIS NMEA sentences from a text file and save to various output formats

    Args:
        filepath(str): full path to the input file containing NMEA sentences
        outpath(str): path to save to excluding file extensions
        debug(bool): create a csv file containing all the individual messages
                     decoded with the original payloads
        jsonverbose(bool): verbose output in the json file
        jsonoutput(bool): save output to json file
        geojsonoutput(bool): save output to geojson file
        csvoutput(bool): save output to csv file
        kmloutput(bool): save output to kml file
    """
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
        except nmea.NMEAInvalidSentence as err:
            AISLOGGER.debug(str(err))
            continue
        except nmea.NMEACheckSumFailed as err:
            AISLOGGER.debug(str(err))
            continue
        except ais.InvalidMMSI as err:
                AISLOGGER.debug(str(err))
                continue
        except ais.UnknownMessageType as err:
            AISLOGGER.debug(str(err))
            AISLOGGER.debug('unknown message - %s', line)
            continue
        except IndexError:
            AISLOGGER.debug('no data on line')
            continue
    stnstats = aistracker.tracker_stats()
    pprint.pprint(stnstats)
    print(nmeatracker.__str__())
    if jsonoutput:
        AISLOGGER.debug('saving JSON output to %s.json', outpath)
        ais.write_json_file(stnstats, outpath + '.json')
    if geojsonoutput:
        AISLOGGER.debug('saving GEOJSON output to %s.geojson', outpath)
        aistracker.create_geojson_map(outpath + '.geojson')
    if csvoutput:
        AISLOGGER.debug('saving CSV output to %s.csv', outpath)
        csvdata = aistracker.create_csv_data()
        ais.write_csv_file(csvdata, outpath + '.csv')
    if kmloutput:
        AISLOGGER.debug('saving KML output to %s.kml', outpath)
        aistracker.create_kml_map(outpath + '.kml', kmzoutput=False)
    if kmzoutput:
        AISLOGGER.debug('saving KML output to %s.kmz', outpath)
        aistracker.create_kml_map(outpath + '.kmz', kmzoutput=True)
    if debug:
        AISLOGGER.info('all decoded AIS messages saved to - %s',
                       outpath + '-messages.csv')
        ais.write_csv_file(messagelist, outpath + '-messages.csv')
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
                       jsonverbose=CLIARGS.v, jsonoutput=CLIARGS.j,
                       geojsonoutput=CLIARGS.g, csvoutput=CLIARGS.c,
                       kmloutput=CLIARGS.kml, kmzoutput=CLIARGS.kmz)
    elif CLIARGS.subcommand == 'net':
        read_from_network(CLIARGS.outputfile)
    else:
        CLIARGS.print_help()

if __name__ == '__main__':
    main()
