# Py AIS NMEA

A program to decode AIS NMEA 0183 sentences. It is written in Python 3.


## Installation

First download or git clone this repo then run.

```
python3 setup.py install
```

## Unit Tests
To run the unit tests.

```
python3 -m unittest pyaisnmea.test_ais
```

## GUI

```
python3 -m pyaisnmea gui
```

Sentences can be either read from a text file or direct from the network.

### To read NMEA sentences from a file:
1. go to File > Open
2. browse to the file to open and click 'Open'
3. if you have selected a plain NMEA0183 text file containing Type 4 messages, a window will appear allowing you to choose an AIS Base Station to use as a timing reference

A sample NMEA 0183 text file has been included for testing. It is called 'sample_nmea.txt'.
This text file contains 10296 NMEA sentences and 10027 AIS messages of 12 different types.

### To read NMEA sentences from the network:
1. go to Network > Settings
2. configure the settings,
   (select 'Network Settings' from the above drop down for details)
3. click the 'Save Settings' button to make changes
4. go to Network > Start Network Server

In server mode the program will listen for incoming AIS NMEA 0183 sentences
from the network.

Server IP - ip of the interface to listen on, set to 0.0.0.0 for all interfaces
Server Port - UDP port to listen on

To forward on the NMEA sentences to another network host, check the box
'forward NMEA sentences to a remote host', then set the 'Remote Server IP' and
'Remote Server Port'.

To log NMEA sentences to a text file, click 'Choose Log Path' and select a
location and filename.

To display AIS locations onto a live kmz map, click 'Choose KMZ Path' and
select an output directory.
Open 'netlink.kml' in Google Earth to view AIS locations.

You must click 'Save Settings' for changes to take effect!

### Stats Tab
This tab contains overall stats about what AIS messages have been processed and
what AIS stations have been seen.

The counters at the top are updated immediately and the 3 text boxes at the
bottom are updated every 10 seconds in server mode.

### Ships Tab
This tab contains a large table of all the AIS Stations.

In server mode this is updated every 10 seconds.

Double clicking on one of the rows will display detailed information for that
station in the 'Station Information' tab.

### Export Tab
This tab allows you to export all the data the AIS decoder currently has.

The export options are:

* OVERVIEW     - export CSV, JSON, KMZ and DEBUG files to a directory
* EVERYTHING   - export overview and data for each AIS station in its own directory
* CSV          - Comma Separated Values file containing similar data to the Ships tab
* TSV          - Tab Separated Values file containing similar data to the Ships tab
* KML          - plain KML file with no custom icons (default icons will be used)
* KMZ          - Keyhole Markup Language Map with custom icons
* JSON         - JSON file containing stats and AIS station last known positions
* VERBOSE JSON - JSON file containing stats and all AIS station position reports
* GEOJSON      - GEOJSON map of all AIS Station positions
* DEBUG        - outputs 2 files (CSV and JSON lines) output of all decoded messages

Data cannot be exported whilst the server is listening.

For KML,KMZ and EVERYTHING output, you can choose to organise the output by Class, Types or Flags.

### Message Log Tab
A table of all the AIS messages.

Double clicking a message will open a window with more detailed information
about that message.

### Station Info Tab
Display detailed information about an AIS Station and its last known location.

KMZ maps of the vessels location and CSV/JSON data of all known positions can be
exported from here using the buttons at the bottom of the tab. All AIS messages for this
particular station can also be exported (format is CSV and JSONL, same as the DEBUG export).

## Command Line

The program can also be run as a command line application.

to view help options run

```
python3 -m pyaisnmea -h

or

python3 -m pyaisnmea <subcommand> -h
```

subcommands are gui, file or livemap

* gui - open the GUI
* file - process a NMEA text file
* livemap - listen for NMEA sentences from the network and plot a live KML map

## Licence

MIT License

Copyright (c) 2020 Thomas W Whittam

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Useful Resources

These are some useful resources that I found helpful whilst creating this software.

* [Maritech Solutions AIS VDM & VDO Message Decoder ](https://www.maritec.co.za/tools/aisvdmvdodecoding/)
* [AIVDM/AIVDO protocol decoding](https://gpsd.gitlab.io/gpsd/AIVDM.html)
* [AIS (Wikipedia)](https://en.wikipedia.org/wiki/Automatic_identification_system)
