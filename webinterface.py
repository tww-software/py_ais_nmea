"""
Flask web frontend for the AIS decoder
"""

import os

import ais
import binary
import icons
import nmea

from flask import Flask, render_template, request, send_file

ICONS = icons.ICONS

STATIONS = {}
POSITIONLOG = {}
STATS = {}
ALLMESSAGES = []
FLAGS = {}
SHIPTYPES = {}
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/headingmap')
def heading_map():
    geojsonfeatures = STATIONS['geojson']
    centrelat = STATIONS['centremap']['Latitude']
    centrelon = STATIONS['centremap']['Longitude']
    return render_template('leafletmap4.html', geojsonfeatures=geojsonfeatures,
                           centrelat=centrelat, centrelon=centrelon,
                           icons=ICONS)


@app.route('/countrymap/<country>')
def country_map(country):
    """
    show only vessels of a certain flag on the map
    """
    countrymmsis = FLAGS[country]
    countrystntracker = ais.AISTracker()
    for mmsi in countrymmsis:
        countrystntracker.stations[mmsi] = STATIONS[mmsi]
    geojsonparser = countrystntracker.create_geojson_map()
    geojsonfeatures = geojsonparser.main["features"]
    centremap = countrystntracker.get_centre_of_map()
    centrelat = centremap['Latitude']
    centrelon = centremap['Longitude']
    return render_template('leafletmap4.html', geojsonfeatures=geojsonfeatures,
                           centrelat=centrelat, centrelon=centrelon,
                           icons=ICONS)


@app.route('/shipmap/<shiptype>')
def ship_map(shiptype):
    """
    show only vessels of a certain ship type on the map
    """
    shiptypemmsis = SHIPTYPES[shiptype]
    shiptypestntracker = ais.AISTracker()
    for mmsi in shiptypemmsis:
        shiptypestntracker.stations[mmsi] = STATIONS[mmsi]
    geojsonparser = shiptypestntracker.create_geojson_map()
    geojsonfeatures = geojsonparser.main["features"]
    centremap = shiptypestntracker.get_centre_of_map()
    centrelat = centremap['Latitude']
    centrelon = centremap['Longitude']
    return render_template('leafletmap4.html', geojsonfeatures=geojsonfeatures,
                           centrelat=centrelat, centrelon=centrelon,
                           icons=ICONS)


@app.route('/positionhistory')
def position_history():
    return render_template('historylog.html', positionlog=POSITIONLOG)

@app.route('/historymap/<timestamp>')
def history_map(timestamp):
    centrelat = POSITIONLOG[timestamp]['mapcentre']['Latitude']
    centrelon = POSITIONLOG[timestamp]['mapcentre']['Longitude']
    geojsonfeatures = POSITIONLOG[timestamp]['geojson']
    return render_template('leafletmap4.html', geojsonfeatures=geojsonfeatures,
                           centrelat=centrelat, centrelon=centrelon,
                           icons=ICONS)

@app.route('/read_capture_file', methods=['GET', 'POST'])
def read_capture_file():
    """
    WORKS
    foutput = 'raw capture file data is displayed here'
    if request.method == 'POST':
        if request.files['file']:
            foutput = request.files['file'].read()
    return render_template('readcapturefile.html', foutput=foutput)
    """
    headers = ['Message Payload', 'Message Type Number',
               'Message Description']
    ALLMESSAGES.append(headers)
    tempcsvpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.csv')
    tempjsonpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.json')
    tempgeojsonpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.geojson')
    tempkmlpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.kmz')
    if request.method == 'GET':
        foutput = []
    elif request.method == 'POST':
        if request.files['file']:
            aistracker = ais.AISTracker()
            nmeatracker = nmea.NMEAtracker()
            for line in request.files['file']:
                line = line.decode('utf-8')
                try:
                    if line == '\n':
                        continue
                    payload = nmeatracker.process_sentence(line)
                    if payload:
                        msglist = []
                        msglist.append(payload)
                        msg = aistracker.process_message(payload)
                        msglist.append(msg.msgtype)
                        msglist.append(msg.__str__())
                        ALLMESSAGES.append(msglist)
                except (IndexError, ais.UnknownMessageType,
                        nmea.NMEACheckSumFailed, nmea.NMEAInvalidSentence,
                        ais.InvalidMMSI):
                    continue
            STATIONS.update(aistracker.stations)
            stnstats = aistracker.tracker_stats()
            organisedmmsis = aistracker.sort_mmsi_by_catagory()
            FLAGS.update(organisedmmsis['Flags'])
            SHIPTYPES.update(organisedmmsis['Subtypes'])
            STATS['Messages'] = stnstats['Message Stats']
            STATS['Times'] = stnstats['Times']
            STATS['TotalNMEASentences'] = nmeatracker.sentencecount
            STATS['MultipartMessagesReassembled'] = nmeatracker.reassembled
            STATS['MessagesRXonchannel'] = nmeatracker.channelcounter
            STATS['AISStationTypes'] = stnstats['AIS Station Types']
            STATS['ShipTypes'] = stnstats['Ship Types']
            STATS['Flags'] = stnstats['Country Flags']
            ais.write_json_file(stnstats, tempjsonpath)
            foutput = aistracker.create_table_data()
            ais.write_csv_file(foutput, tempcsvpath)
            aistracker.create_kml_map(tempkmlpath)
            geojsonparser = aistracker.create_geojson_map(tempgeojsonpath)
            STATIONS['geojson'] = geojsonparser.main["features"]
            STATIONS['centremap'] = aistracker.get_centre_of_map()
            poslogs = aistracker.position_log()
            POSITIONLOG.update(poslogs)
    return render_template('readcapturefile.html', foutput=foutput)

@app.route('/msgdebug_capture_file')
def msgdebug_capture_file():
    """
    read a capture file and list all the individual messages
    """
    return render_template('msgdebug.html', allmessages=ALLMESSAGES)

@app.route('/stats')
def stats():
    return render_template('stats.html', stats=STATS, icons=ICONS)

@app.route('/aisstation/<mmsi>')
def station_details(mmsi):
    station = STATIONS[mmsi].__dict__
    tempkmlpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', mmsi + '.kmz')
    singlestntracker = ais.AISTracker()
    singlestntracker.stations[mmsi] = STATIONS[mmsi]
    try:
        singlestntracker.create_kml_map(tempkmlpath)
        lastpos = STATIONS[mmsi].get_latest_position()
        geojsonparser = singlestntracker.create_geojson_map()
        geojsonfeatures = geojsonparser.main["features"]
        centremap = singlestntracker.get_centre_of_map()
        centrelat = centremap['Latitude']
        centrelon = centremap['Longitude']
        return render_template('ais_station.html', station=station,
                               lastpos=lastpos,
                               icons=ICONS,
                               geojsonfeatures=geojsonfeatures,
                               centrelat=centrelat, centrelon=centrelon)
    except ais.NoSuitablePositionReport:
        return render_template('ais_station_no_location.html', station=station)

@app.route('/<mmsi>.kmz')
def stn_kml_file(mmsi):
    tempkmlpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', mmsi + '.kmz')
    return send_file(tempkmlpath, mimetype='application/zip')

@app.route('/temp.csv')
def temp_csv_file():
    temppath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.csv')
    return send_file(temppath, mimetype='application/csv')

@app.route('/temp.kmz')
def temp_kml_file():
    temppath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.kmz')
    return send_file(temppath, mimetype='application/zip')

@app.route('/temp.json')
def temp_json_file():
    temppath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.json')
    return send_file(temppath, mimetype='application/json')

@app.route('/temp.geojson')
def temp_geojson_file():
    temppath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', 'temp.geojson')
    return send_file(temppath, mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)
