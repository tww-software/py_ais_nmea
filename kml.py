"""
a parser to generate Keyhole Markup Language (KML) for Google Earth
"""


class KMLOutputParser():
    """
    Class to parse KML into an output file.
    """
    def __init__(self, kmlfilepath):
        self.kmlfilepath = kmlfilepath
        self.kmlheader = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>Ships</name>
<open>1</open>
<Style id="Base Station">
<IconStyle>
<scale>1.5</scale>
<Icon>
<href>icons/basestn.png</href>
</Icon>
<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>
<Style id="Class B">
<IconStyle>
<scale>1.5</scale>
<Icon>
<href>icons/classb.png</href>
</Icon>
<hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>
<Style id="SAR Aircraft">
<IconStyle>
<scale>1.5</scale>
<Icon>
<href>icons/sar.png</href>
</Icon>
<hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>
<Style id="Class A">
<IconStyle>
<scale>1.5</scale>
<Icon>
<href>icons/classa.png</href>
</Icon>
<hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>
<Style id="Navigation Aid">
<IconStyle>
<scale>1.4</scale>
<Icon>
<href>icons/navaid.png</href>
</Icon>
<hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>
<Style id="not specified">
<IconStyle>
<scale>1.4</scale>
<Icon>
<href>icons/unknown.png</href>
</Icon>
<hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/>
</IconStyle>
<ListStyle>
</ListStyle>
</Style>"""
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
            if item == 'posrep':
                continue
            if item == 'sentmsgs':
                continue
            elif item == 'details':
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

    def create_kml_header(self):
        """
        Write the first part of the KML output file.
        This only needs to be called once at the start of the kml file.
        """
        with open(self.kmlfilepath, 'w') as kmlout:
            kmlout.write(self.kmlheader)

    def add_kml_placemark(self, placemarkname, description, lon, lat, style):
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
        placemark = self.placemarktemplate % (placemarkname, description,
                                              lon, lat, style, coords)
        with open(self.kmlfilepath, 'a') as kmlout:
            kmlout.write(placemark)

    def open_folder(self, foldername):
        """
        open a folder to store placemarks

        Args:
            foldername(str): the name of the folder
        """
        openfolderstr = "<Folder>\n<name>{}</name>".format(foldername)
        with open(self.kmlfilepath, 'a') as kmlout:
            kmlout.write(openfolderstr)

    def close_folder(self):
        """
        close the currently open folder
        """
        closefolderstr = "</Folder>"
        with open(self.kmlfilepath, 'a') as kmlout:
            kmlout.write(closefolderstr)

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
        with open(self.kmlfilepath, 'a') as kmlout:
            kmlout.write(placemark)

    def close_kml_file(self):
        """
        Write the end of the KML file.
        This needs to be called once at the end of the file
        to ensure the tags are closed properly.
        """
        endtags = "\n</Document></kml>"
        with open(self.kmlfilepath, 'a') as kmlout:
            kmlout.write(endtags)
