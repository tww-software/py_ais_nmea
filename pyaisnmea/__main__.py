"""
command line interface for processing AIS traffic
"""

import argparse
import logging

import pyaisnmea.capturefile as capturefile
import pyaisnmea.gui.basicgui as basicgui
import pyaisnmea.livekmlmap as livekmlmap
import pyaisnmea.version as version


def cli_arg_parser():
    """
    get the cli arguments and run the program

    Returns:
        parser(argparse.ArgumentParser): the command line options parser
    """
    desc = 'tool to decode AIS traffic and generate meaningful data'
    versiontxt = 'pyaisnmea version = {}'.format(version.VERSION)
    parser = argparse.ArgumentParser(description=desc, epilog=versiontxt)
    parser.add_argument('-v', action='store_true', help='verbose output')
    parser.add_argument('--version', action='version', version=versiontxt)
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.add_parser('gui', help=('open the GUI'))

    livemapparser = subparsers.add_parser(
        'livemap',
        help=('read AIS traffic from a UDP network port and create a '
              'live updating KML map'))
    livemapparser.add_argument(help=('output directory path, directory '
                                     'to write kml files to'),
                               dest='outputdir')
    livemaptype = livemapparser.add_mutually_exclusive_group()
    livemaptype.add_argument(
        '-a', action='store_true',
        help='advanced kml map with custom ship icons and headings')
    livemaptype.add_argument('-b', action='store_true', help='basic kml map')
    mapialaregion = livemapparser.add_mutually_exclusive_group()
    mapialaregion.add_argument(
        '-A', action='store_true', help='IALA region A (default)')
    mapialaregion.add_argument('-B', action='store_true', help='IALA region B')
    mapfileorder = livemapparser.add_mutually_exclusive_group()
    mapfileorder.add_argument(
        '-fl', action='store_true', help='order output by flags')
    mapfileorder.add_argument(
        '-cl', action='store_true', help='order output by class')
    mapfileorder.add_argument(
        '-ty', action='store_true', help='order output by types (default)')
    fileparser = subparsers.add_parser('file',
                                       help=('read AIS traffic '
                                             'from a capture file'))
    fileparser.add_argument(help='input file path', dest='inputfile')
    ehelp = ('Everything - '
             'output individual KMZ, CSV and JSON Lines for each AIS Station')
    fileparser.add_argument(dest='outputdir', help='output directory path')
    fileparser.add_argument('-e', action='store_true', help=ehelp)
    filetype = fileparser.add_mutually_exclusive_group()
    filetype.add_argument('-t', action='store_true', help='import text file')
    filetype.add_argument('-c', action='store_true', help='import CSV file')
    filetype.add_argument(
        '-j', action='store_true', help='import JSON lines file')
    ialaregion = fileparser.add_mutually_exclusive_group()
    ialaregion.add_argument(
        '-A', action='store_true', help='IALA region A (default)')
    ialaregion.add_argument('-B', action='store_true', help='IALA region B')
    fileorder = fileparser.add_mutually_exclusive_group()
    fileorder.add_argument(
        '-fl', action='store_true', help='order output by flags')
    fileorder.add_argument(
        '-cl', action='store_true', help='order output by class')
    fileorder.add_argument(
        '-ty', action='store_true', help='order output by types (default)')
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
    if cliargs.subcommand == 'gui':
        aisgui = basicgui.BasicGUI()
        aisgui.mainloop()
    elif cliargs.subcommand == 'file':
        if cliargs.fl:
            orderby = 'Flags'
        elif cliargs.cl:
            orderby = 'Class'
        else:
            orderby = 'Types'
        if cliargs.B:
            region = 'B'
        else:
            region = 'A'
        if (cliargs.t or
                cliargs.inputfile.endswith('.txt') or
                cliargs.inputfile.endswith('.nmea')):
            capturefile.read_from_file(
                cliargs.inputfile, cliargs.outputdir,
                everything=cliargs.e, filetype='text',
                orderby=orderby, region=region)
        elif cliargs.c or cliargs.inputfile.endswith('.csv'):
            capturefile.read_from_file(
                cliargs.inputfile, cliargs.outputdir,
                everything=cliargs.e, filetype='csv',
                orderby=orderby, region=region)
        elif cliargs.j or cliargs.inputfile.endswith('.jsonl'):
            capturefile.read_from_file(
                cliargs.inputfile, cliargs.outputdir,
                everything=cliargs.e, filetype='jsonlines',
                orderby=orderby, region=region)
        else:
            capturefile.read_from_file(
                cliargs.inputfile, cliargs.outputdir, everything=cliargs.e,
                orderby=orderby, region=region)
    elif cliargs.subcommand == 'livemap':
        if cliargs.fl:
            orderby = 'Flags'
        elif cliargs.cl:
            orderby = 'Class'
        else:
            orderby = 'Types'
        if cliargs.B:
            region = 'B'
        else:
            region = 'A'
        if cliargs.a:
            kmzoutput = True
        elif cliargs.b:
            kmzoutput = False
        if cliargs.a or cliargs.b:
            livemap = livekmlmap.LiveKMLMap(
                cliargs.outputdir, kmzoutput=kmzoutput,
                orderby=orderby, region=region)
            livemap.create_netlink_file()
            livemap.start_server()
            livemap.get_nmea_sentences()
        else:
            cliparser.print_help()
    else:
        cliparser.print_help()


if __name__ == '__main__':
    main()
