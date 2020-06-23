"""
command line interface for processing AIS traffic
"""

import argparse
import logging

import pyaisnmea.capturefile as capturefile
import pyaisnmea.gui.basicgui as basicgui
import pyaisnmea.livekmlmap as livekmlmap
import pyaisnmea.version as version


AISLOGGER = logging.getLogger(__name__)


def cli_arg_parser():
    """
    get the cli arguments and run the program

    Returns:
        parser(argparse.ArgumentParser): the command line options parser
    """
    desc = 'tool to decode AIS traffic and generate meaningful data'
    versiontxt = 'version = {}'.format(version.VERSION)
    parser = argparse.ArgumentParser(description=desc, epilog=versiontxt)
    parser.add_argument('-v', action='store_true', help='verbose output')
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
    fileparser = subparsers.add_parser('file',
                                       help=('read AIS traffic '
                                             'from a capture file'))
    fileparser.add_argument(help='input file path', dest='inputfile')
    fileparser.add_argument(help='output directory path', dest='outputdir')
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
                                     'file then decode and output all '
                                     'AIS messages into a csv and json lines '
                                     'file'))
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
        capturefile.read_from_file(
            cliargs.inputfile, cliargs.outputdir, cliargs.d,
            jsonoutput=cliargs.j,
            geojsonoutput=cliargs.g, csvoutput=cliargs.c,
            tsvoutput=cliargs.t,
            kmloutput=cliargs.kml, kmzoutput=cliargs.kmz,
            verbosejson=cliargs.v)
    elif cliargs.subcommand == 'livemap':
        if cliargs.a:
            kmzoutput = True
        elif cliargs.b:
            kmzoutput = False
        if cliargs.a or cliargs.b:
            livemap = livekmlmap.LiveKMLMap(
                cliargs.outputdir, kmzoutput=kmzoutput)
            livemap.create_netlink_file()
            livemap.start_server()
            livemap.get_nmea_sentences()
        else:
            cliparser.print_help()
    else:
        cliparser.print_help()


if __name__ == '__main__':
    main()
