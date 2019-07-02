"""
Module to output GeoJSON
"""


import json


class GeoJsonParser():
    """
    Simple parser to generate a dictionary that can be used with json.dump(s)

    Attributes:
        main(dict): main dictionary to store all the points and linestrings
    """

    def __init__(self):
        self.main = {"type": "FeatureCollection", "features": []}

    @staticmethod
    def create_feature_point(lon, lat, properties):
        """
        create a single point on the map

        Args:
            lat(float): latitude
            lon(float): longitude
            properties(dict): dictionary of info about this point

        Returns:
            fpoint(dict): dictionary for a GeoJSON point
        """
        fpoint = {"type": "Feature", "geometry": {"type": "Point",
                                                  "coordinates": [lon, lat]},
                  "properties": properties}
        return fpoint

    @staticmethod
    def create_feature_linestring(coords, properties):
        """
        create a line made up of multiple co-ordinates

        Args:
            coords(list): list of lists each containing 2 elements latitude
                          and longitude
            properties(dict): dictionary of info about this linestring

        Returns:
            flinestring(dict): dictionary for a GeoJSON line string
        """
        flinestring = {"type": "Feature", "geometry": {"type": "LineString",
                                                       "coordinates": coords},
                       "properties": properties}
        return flinestring

    def add_station_info(self, mmsi, properties, coords, lastlon, lastlat):
        """
        add information for a AIS station consisting of a point
        of the last known position and a linestring of past positions

        Args:
            mmsi(int): the MMSI for the AIS station
            properties(dict): dictionary of info relating to the AIS station
            coords(list): list of lists, each individual list should contain
                          the longitude and then the latitude
            lastlon(float): the last known longitude
            lastlat(float): the last known latitude
        """
        shippoint = self.create_feature_point(lastlon, lastlat, properties)
        self.main["features"].append(shippoint)
        if len(coords) > 1:
            linestringinfo = {"MMSI": mmsi}
            shiplinestring = self.create_feature_linestring(coords,
                                                            linestringinfo)
            self.main["features"].append(shiplinestring)

    def add_station_point(self, properties, lastlon, lastlat):
        """
        add information for a AIS station consisting of a point
        of the last known position

        Note:
            no linestring is created, this just creates a point
            this is used for live mapping

        Args:
            properties(dict): dictionary of info relating to the AIS station
            lastlon(float): the last known longitude
            lastlat(float): the last known latitude
        """
        shippoint = self.create_feature_point(lastlon, lastlat, properties)
        self.main["features"].append(shippoint)

    def save_to_file(self, outputfilepath):
        """
        save the GeoJSON to a file

        Args:
            outputfilepath(str or path like object): where to save to
        """
        with open(outputfilepath, 'w') as geojsonfile:
            json.dump(self.main, geojsonfile)

    def get_json_string(self):
        """
        get the self.main JSON as a string

        Returns:
            geojson(str): the JSON representation of self.main as a string
        """
        geojson = json.dumps(self.main)
        return geojson
