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
STATS = {}
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

@app.route('/map')
def map():
    geojsonfeatures = STATIONS['geojson']
    centrelat = STATIONS['centremap']['Latitude']
    centrelon = STATIONS['centremap']['Longitude']
    return render_template('leafletmap2.html', geojsonfeatures=geojsonfeatures,
                           centrelat=centrelat, centrelon=centrelon)

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
        nmeastats = ''
        aisstats = ''
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
                        msg = aistracker.process_message(payload)
                except (IndexError, ais.UnknownMessageType,
                        nmea.NMEACheckSumFailed, nmea.NMEAInvalidSentence):
                    continue
            STATIONS.update(aistracker.stations)
            stnstats = aistracker.all_station_info(verbose=False)
            STATS['Messages'] = stnstats['Message Stats']
            STATS['Times'] = stnstats['Times']
            STATS['TotalNMEASentences'] = nmeatracker.sentencecount
            STATS['MultipartMessagesReassembled'] = nmeatracker.reassembled
            STATS['MessagesRXonchannel'] = nmeatracker.channelcounter
            STATS['AISStationTypes'] = stnstats['AIS Station Types']
            STATS['ShipTypes'] = stnstats['Ship Types']
            ais.write_json_file(stnstats, tempjsonpath)
            foutput = aistracker.create_csv_data()
            ais.write_csv_file(foutput, tempcsvpath)
            aistracker.create_kml_map(tempkmlpath)
            geojsonparser = aistracker.create_geojson_map(tempgeojsonpath)
            STATIONS['geojson'] = geojsonparser.main["features"]
            STATIONS['centremap'] = aistracker.get_centre_of_map()
    return render_template('readcapturefile.html', foutput=foutput)

@app.route('/msgdebug_capture_file', methods=['GET', 'POST'])
def msgdebug_capture_file():
    """
    read a capture file and list all the individual messages
    """
    headers = ['Message Payload', 'Message Type Number',
               'Message Description']
    allmessages = []
    allmessages.append(headers)
    if request.method == 'GET':
        foutput = []
        nmeastats = ''
        aisstats = ''
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
                        allmessages.append(msglist)
                except (IndexError, ais.UnknownMessageType,
                        nmea.NMEACheckSumFailed, nmea.NMEAInvalidSentence):
                    continue
            nmeastats = nmeatracker.__str__()
            aisstats = aistracker.__str__()
    return render_template('msgdebug.html', allmessages=allmessages,
                           nmeastats=nmeastats, aisstats=aisstats)

@app.route('/stats')
def stats():
    return render_template('stats.html', stats=STATS, icons=ICONS)

@app.route('/aisstation/<mmsi>')
def station_details(mmsi):
    station = STATIONS[int(mmsi)].__dict__
    tempkmlpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', mmsi + '.kmz')
    singlestntracker = ais.AISTracker()
    singlestntracker.stations[mmsi] = STATIONS[int(mmsi)]
    singlestntracker.create_kml_map(tempkmlpath)
    lastpos = STATIONS[int(mmsi)].get_latest_position()
    if lastpos != 'Unknown':
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
    else:
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
