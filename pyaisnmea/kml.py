"""
a parser to generate Keyhole Markup Language (KML) for Google Earth
"""

import datetime
import os
import re
import zipfile

import pyaisnmea.icons as icons


DATETIMEREGEX = re.compile(
    r'\d{4}/(0[1-9]|1[0-2])/(0[1-9]|1[0-9]|2[0-9]|3[01]) '
    r'(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])')


class KMLOutputParser():
    """
    Class to parse KML into an output file.

    Attributes:
        kmldoc(list): list of strings to make up the doc.kml
        kmlfilepath(str): path to output KML file
        kmlheader(str): first part of a KML file
        placemarktemplate(str): template for a KML placemark (pin on map)
        lineplacemarktemplate(str): template for KML linestring (line on map)
        styletemplate(str): template for custom icons on placemarks
        greenarrowtemplate(str): template for green (heading) arrows
        orangearrowtemplate(str): template for orange (CoG) arrows
    """
    def __init__(self, kmlfilepath):
        self.kmldoc = []
        self.kmlfilepath = kmlfilepath
        self.kmlheader = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>Ships</name>
<open>1</open>"""
        self.placemarktemplate = """
<Placemark>
<name>%s</name>
<description>%s</description>
<TimeStamp>
<when>%s</when>
</TimeStamp>
<LookAt>
<longitude>%s</longitude>
<latitude>%s</latitude>
<altitude>%s</altitude>
<heading>-0</heading>
<tilt>0</tilt>
<range>500</range>
</LookAt>
<styleUrl>#%s</styleUrl>
<Point>
<altitudeMode>absolute</altitudeMode>
<coordinates>%s</coordinates>
</Point>
</Placemark>"""
        self.lineplacemarktemplate = """
<Placemark>
<name>%s</name>
<LineString>
<altitudeMode>absolute</altitudeMode>
<coordinates>%s</coordinates>
</LineString>
</Placemark>"""
        self.styletemplate = """
<Style id="%s">
<IconStyle>
<scale>2.8</scale>
<Icon>
<href>icons/%s</href>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>"""
        self.greenarrowtemplate = """
<Style id="%s">
<IconStyle>
<scale>2.8</scale>
<Icon>
<href>green_arrows/%s</href>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>"""
        self.orangearrowtemplate = """
<Style id="%s">
<IconStyle>
<scale>2.8</scale>
<Icon>
<href>orange_arrows/%s</href>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>"""

    @staticmethod
    def format_kml_placemark_description(placemarkdict):
        """
        format html tags for inside a kml placemark from a dictionary

        Args:
            placemarkdict(dict): dictionary of information for a placemark

        Returns:
            description(str): the dictionary items formatted as HTML string
                              suitable to be in a KML placemark description
        """
        starttag = "<![CDATA["
        newlinetag = "<br  />\n"
        endtag = "]]>"
        descriptionlist = []
        descriptionlist.append(starttag)
        for item in placemarkdict:
            if isinstance(placemarkdict[item], dict):
                descriptionlist.append(newlinetag)
                descriptionlist.append(item.upper())
                descriptionlist.append(newlinetag)
                for subitem in placemarkdict[item]:
                    descriptionlist.append(str(subitem).upper())
                    descriptionlist.append(' - ')
                    descriptionlist.append(str(placemarkdict[item][subitem]))
                    descriptionlist.append(newlinetag)
                continue
            descriptionlist.append(str(item).upper())
            descriptionlist.append(' - ')
            descriptionlist.append(str(placemarkdict[item]))
            descriptionlist.append(newlinetag)
        descriptionlist.append(endtag)
        description = ''.join(descriptionlist)
        return description

    def create_kml_header(self, kmz=True, iconsused='all'):
        """
        Write the first part of the KML output file.
        This only needs to be called once at the start of the kml file.

        Args:
            kmz(bool): is this for a KMZ file or not?
            iconsused(str): do we use 'all' the icons (default)
                            or specify a single icon?
        """
        self.kmldoc.append(self.kmlheader)
        if kmz:
            if iconsused == 'all':
                for icontype in icons.ICONS:
                    iconkml = self.styletemplate % (icontype,
                                                    icons.ICONS[icontype])
                    self.kmldoc.append(iconkml)
            else:
                try:
                    iconkml = self.styletemplate % (
                        iconsused, icons.ICONS[iconsused])
                except KeyError:
                    iconkml = self.styletemplate % (
                        iconsused, icons.ICONS['Unknown'])
                self.kmldoc.append(iconkml)
            for heading in range(0, 360):
                thiconkml = self.greenarrowtemplate % (
                    str(heading) + 'TH', str(heading) + '.png')
                cogiconkml = self.orangearrowtemplate % (
                    str(heading) + 'CoG', str(heading) + '.png')
                self.kmldoc.append(thiconkml)
                self.kmldoc.append(cogiconkml)

    def add_kml_placemark(self, placemarkname, description, lon, lat, style,
                          altitude='0', kmz=True, timestamp=''):
        """
        Write a placemark to the KML file (a pin on the map!)

        Args:
            placemarkname(str): text that appears next to the pin on the map
            description(str): text that will appear in the placemark
            lon(str): longitude in decimal degrees
            lat(str): latitude in decimal degrees
            style(str): icon to use
            altitude(str): altitude in metres
            kmz(bool): are we using the custom icons for a KMZ file?
            timestamp(str): time stamp in XML format
        """
        placemarkname = remove_invalid_chars(placemarkname)
        coords = lon + ',' + lat + ',' + altitude
        if not kmz:
            style = ''
        placemark = self.placemarktemplate % (
            placemarkname, description, timestamp, lon, lat,
            altitude, style, coords)
        self.kmldoc.append(placemark)

    def open_folder(self, foldername):
        """
        open a folder to store placemarks

        Args:
            foldername(str): the name of the folder
        """
        cleanfoldername = remove_invalid_chars(foldername)
        openfolderstr = "<Folder>\n<name>{}</name>".format(cleanfoldername)
        self.kmldoc.append(openfolderstr)

    def close_folder(self):
        """
        close the currently open folder
        """
        closefolderstr = "</Folder>"
        self.kmldoc.append(closefolderstr)

    def add_kml_placemark_linestring(self, placemarkname, coords):
        """
        Write a linestring to the KML file (a line on the map!)

        Args:
            placemarkname(str): name of the linestring
            coords(list): list of dicts containing Lat/Lon
        """
        placemarkname = remove_invalid_chars(placemarkname)
        newcoordslist = []
        for item in coords:
            lon = str(item['Longitude'])
            lat = str(item['Latitude'])
            try:
                alt = str(item['Altitude (m)'])
            except KeyError:
                alt = '0'
            coordsline = '{},{},{}'.format(lon, lat, alt)
            newcoordslist.append(coordsline)
        placemark = self.lineplacemarktemplate % (placemarkname,
                                                  '\n'.join(newcoordslist))
        self.kmldoc.append(placemark)

    def close_kml_file(self):
        """
        Write the end of the KML file.
        This needs to be called once at the end of the file
        to ensure the tags are closed properly.
        """
        endtags = "\n</Document></kml>"
        self.kmldoc.append(endtags)

    def write_kml_doc_file(self):
        """
        write the tags to the kml doc.kml file
        """
        with open(self.kmlfilepath, 'w') as kmlout:
            for kmltags in self.kmldoc:
                kmlout.write(kmltags)


class InvalidDateTimeString(Exception):
    """
    raise if timestamp is the wrong format
    """


def make_kmz(kmzoutputfilename, iconslist=set(icons.ICONS.values()),
             greenarrows=range(0, 360), orangearrows=range(0, 360)):
    """
    make a kmz file out of the doc.kml and symbols directory

    Args:
        kmzoutputfilename(str): full path to the .kmz file to output
        iconslist(list): list of icons required
    """
    docpath = os.path.join(os.path.dirname(kmzoutputfilename), 'doc.kml')
    iconspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'static', 'icons')
    greenarrowspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'static', 'green_arrows')
    orangearrowspath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'static', 'orange_arrows')
    with zipfile.ZipFile(kmzoutputfilename,
                         'w', zipfile.ZIP_DEFLATED, False) as kmz:
        try:
            kmz.debug = 3
            kmz.write(docpath, 'doc.kml')
            for icon in iconslist:
                kmz.write(os.path.join(iconspath, icon),
                          os.path.join('icons', icon))
            for arrow in greenarrows:
                kmz.write(os.path.join(greenarrowspath, str(arrow) + '.png'),
                          os.path.join('green_arrows', str(arrow) + '.png'))
            for arrow in orangearrows:
                kmz.write(os.path.join(orangearrowspath, str(arrow) + '.png'),
                          os.path.join('orange_arrows', str(arrow) + '.png'))
            os.remove(docpath)
        except Exception as err:
            print('zip error')
            print(str(err))


def remove_invalid_chars(xmlstring):
    """
    remove invalid chars from a string

    Args:
        xmlstring(str): input string to clean

    Returns:
        cleanstring(str): return string with invalid chars replaced or removed
    """
    invalidchars = {'<': '&lt;', '>': '&gt;', '"': '&quot;',
                    '\t': '    ', '\n': ''}
    cleanstring = xmlstring.replace('&', '&amp;')
    for invalidchar in invalidchars:
        cleanstring = cleanstring.replace(
            invalidchar, invalidchars[invalidchar])
    return cleanstring


def convert_timestamp_to_kmltimestamp(timestamp):
    """
    convert the pyais timestamp string to one suitable for KML

    Args:
        timestamp(str): the timestamp string in the format '%Y/%m/%d %H:%M:%S'

    Raises:
        InvalidDateTimeString: when the timestamp is not correctly formatted

    Returns:
        xmltimestamp(str): the timestamp in the format '%Y-%m-%dT%H:%M:%SZ'
    """
    if DATETIMEREGEX.match(timestamp):
        if timestamp.endswith(' (estimated)'):
            timestamp = timestamp.rstrip(' (estimated)')
        try:
            dtobj = datetime.datetime.strptime(timestamp, '%Y/%m/%d %H:%M:%S')
            kmltimestamp = dtobj.strftime('%Y-%m-%dT%H:%M:%SZ')
        except ValueError as err:
            raise InvalidDateTimeString('wrong') from err
        return kmltimestamp
    raise InvalidDateTimeString('timestamp must be %Y/%m/%d %H:%M:%S')
