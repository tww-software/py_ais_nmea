"""
command line interface for processing AIS traffic
"""

import argparse
import logging

import capturefile
import gui
import network


AISLOGGER = logging.getLogger(__name__)


def cli_arg_parser():
    """
    get the cli arguments and run the program

    Returns:
        parser(argparse.ArgumentParser): the command line options parser
    """
    desc = 'tool to decode AIS traffic and generate meaningful data'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-v', action='store_true', help='verbose output')
    parser.add_argument('-g', action='store_true', help='open the GUI')
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
    outputformats.add_argument('-t', action='store_true', help='tsv output')
    outputformats.add_argument('-d', action='store_true',
                               help=('read AIS traffic from a capture '
                                     'file then decode and display all'
                                     ' the messages individually'))
    return parser


def main():
    """
    get the command line arguments and decide what to run
    """
    cliparser = cli_arg_parser()
    cliargs = cliparser.parse_args()
    if cliargs.v:
        logging.basicConfig(level=logging.DEBUG,
                            handlers=[logging.StreamHandler()])
        logging.debug('verbose logging selected')
    else:
        logging.basicConfig(level=logging.INFO,
                            handlers=[logging.StreamHandler()])
    if cliargs.g:
            aisgui = gui.BasicGUI()
            aisgui.display_gui()
    elif cliargs.subcommand == 'file':
        capturefile.read_from_file(
            cliargs.inputfile, cliargs.outputfile, cliargs.d,
            jsonoutput=cliargs.j,
            geojsonoutput=cliargs.g, csvoutput=cliargs.c,
            tsvoutput=cliargs.t,
            kmloutput=cliargs.kml, kmzoutput=cliargs.kmz)
    elif cliargs.subcommand == 'net':
        network.read_from_network(cliargs.outputfile)
    else:
        cliparser.print_help()


if __name__ == '__main__':
    main()
