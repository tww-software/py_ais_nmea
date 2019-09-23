"""
a parser to generate Keyhole Markup Language (KML) for Google Earth
"""

import os
import zipfile

import icons


class KMLOutputParser():
    """
    Class to parse KML into an output file.
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
<LookAt>
<longitude>%s</longitude>
<latitude>%s</latitude>
<altitude>0</altitude>
<heading>-0</heading>
<tilt>0</tilt>
<range>500</range>
</LookAt>
<styleUrl>#%s</styleUrl>
<Point>
<coordinates>%s</coordinates>
</Point>
</Placemark>"""
        self.lineplacemarktemplate = """
<Placemark>
<name>%s</name>
<LineString>
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
        self.arrowtemplate = """
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

    @staticmethod
    def format_kml_placemark_description(placemarkdict):
        """
        format html tags for inside a kml placemark from a dictionary

        Args:
            placemarkdict(dict): dictionary of information for a placemark
        """
        starttag = "<![CDATA["
        newlinetag = "<br  />\n"
        endtag = "]]>"
        descriptionlist = []
        descriptionlist.append(starttag)
        for item in placemarkdict:
            if item == 'Last Known Position':
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

    def create_kml_header(self, kmz=True):
        """
        Write the first part of the KML output file.
        This only needs to be called once at the start of the kml file.
        """
        self.kmldoc.append(self.kmlheader)
        if kmz:
            for icontype in icons.ICONS:
                iconkml = self.styletemplate % (icontype,
                                                icons.ICONS[icontype])
                self.kmldoc.append(iconkml)
            for heading in range(0, 360):
                iconkml = self.arrowtemplate % (heading, str(heading) + '.png')
                self.kmldoc.append(iconkml)

    def add_kml_placemark(self, placemarkname, description, lon, lat, style,
                          kmz=True):
        """
        Write a placemark to the KML file (a pin on the map!)

        Args:
            placemarkname(str): text that appears next to the pin on the map
            description(str): text that will appear in the placemark
            lon(str): longitude in decimal degrees
            lat(str): latitude in decimal degrees
            style(str): icon to use
        """
        coords = lon + ',' + lat + ',0'
        if not kmz:
            style = ''
        placemark = self.placemarktemplate % (placemarkname, description,
                                              lon, lat, style, coords)
        self.kmldoc.append(placemark)

    def open_folder(self, foldername):
        """
        open a folder to store placemarks

        Args:
            foldername(str): the name of the folder
        """
        openfolderstr = "<Folder>\n<name>{}</name>".format(foldername)
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
        newcoordslist = []
        for item in coords:
            coordsline = '{},{},0'.format(str(item['Longitude']),
                                          str(item['Latitude']))
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


def make_kmz(kmzoutputfilename):
    """
    make a kmz file out of the doc.kml and symbols directory
    """
    docpath = os.path.join(os.path.dirname(kmzoutputfilename), 'doc.kml')
    iconspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'static', 'icons')
    arrowspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              'static', 'green_arrows')
    with zipfile.ZipFile(kmzoutputfilename,
                         'w', zipfile.ZIP_DEFLATED, False) as kmz:
        try:
            kmz.debug = 3
            kmz.write(docpath, 'doc.kml')
            for icon in os.listdir(iconspath):
                kmz.write(os.path.join(iconspath, icon),
                          os.path.join('icons', icon))
            for arrow in os.listdir(arrowspath):
                kmz.write(os.path.join(arrowspath, arrow),
                          os.path.join('green_arrows', arrow))
            os.remove(docpath)
        except Exception as err:
            print('zip error')
            print(str(err))
