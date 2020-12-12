"""
help windows and documentation for the AIS decoder GUI
"""

import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.ttk


import pyaisnmea.version as version
import pyaisnmea.gui.exporttab as exporttab

INTRO = """
This program is designed to decode AIS NMEA 0183 sentences.

Sentences can be either read from a text file or direct from the network.

To read NMEA sentences from a file:
1. go to File > Open
2. browse to the file to open and click 'Open', select what type of file
   you want to import using the 'Files of type' dropdown
3. if you have selected a plain NMEA0183 text file containing Type 4 messages,
   a window will appear allowing you to choose an AIS Base Station (or multiple
   AIS Base Stations to use as a timing reference

JSON Lines and CSV files previously exported by PYAISNMEA can also be imported.

To read NMEA sentences from the network:
1. go to Network > Settings
2. configure the settings,
   (select 'Network Settings' from the above drop down for details)
3. click the 'Save Settings' button to make changes
4. go to Network > Start Network Server
"""

LICENCE = """

Version {}

MIT License

Copyright (c) {} Thomas W Whittam

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
""".format(version.VERSION, version.YEAR)


NETWORKSETTINGS = """
Settings for the network server.

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
This is an experimental feature.

You must click 'Save Settings' for changes to take effect!
"""


STATS = """
This tab contains overall stats about what AIS messages have been processed and
what AIS stations have been seen.

The counters at the top are updated immediately and the 3 text boxes at the
bottom are updated every 10 seconds in server mode.
"""


SHIPS = """
This tab contains a large table of all the AIS Stations.

In server mode this is updated every 10 seconds.

Double clicking on one of the rows will display detailed information for that
station in the 'Station Information' tab.
"""

EXPORTHELPLIST = []
for key, var in exporttab.EXPORTHELP.items():
    EXPORTHELPLIST.append('{} - {}'.format(key, var))
EXPORTHELP = '\n'.join(EXPORTHELPLIST)
EXPORT = """
This tab allows you to export all the data the AIS decoder currently has.

The export options are:

{}

Data cannot be exported whilst the server is listening.

For KML,KMZ and EVERYTHING output, you can choose to organise
the output by Class, Types or Flags.
""".format(EXPORTHELP)


MSGLOG = """
A table of all the AIS messages.

Double clicking a message will open a window with more detailed information
about that message.

Right click will select all text, ctrl + c to copy it to the clipboard.
"""


STNINFO = """
Display detailed information about an AIS Station and its last known location.

KMZ maps of the vessels location, CSV and JSON data of all known positions
can be exported from here using the buttons at the bottom of the tab.
"""


class HelpTab(tkinter.ttk.Frame):
    """
    tab to provide a help description

    Args:
        window(tkinter.Toplevel): the help window to attach this frame to
    """

    help = {'Introduction': INTRO,
            'Stats Tab': STATS,
            'Ships Tab': SHIPS,
            'Export Tab': EXPORT,
            'Message Log Tab': MSGLOG,
            'Station Information Tab': STNINFO,
            'Network Settings': NETWORKSETTINGS,
            'Licence': LICENCE}

    def __init__(self, window):
        tkinter.ttk.Frame.__init__(self, window)
        self.helpoptions = tkinter.ttk.Combobox(self, state='readonly')
        self.helpoptions.pack(side='top')
        self.helptxt = tkinter.scrolledtext.ScrolledText(self)
        self.helptxt.pack(side='left', fill='both', expand=tkinter.TRUE)
        self.helpoptions['values'] = list(self.help.keys())
        self.helptxt.delete(1.0, tkinter.END)
        self.helptxt.insert(tkinter.INSERT, self.help['Introduction'])
        self.helpoptions.bind("<<ComboboxSelected>>", self.show_help)

    def show_help(self, event=None):
        """
        show help topic
        """
        self.helptxt.delete(1.0, tkinter.END)
        helptopic = self.helpoptions.get()
        if helptopic != '':
            try:
                self.helptxt.insert(tkinter.INSERT, self.help[helptopic])
            except KeyError:
                tkinter.messagebox.showerror(
                    'AIS Decoder Help',
                    'no help for topic - {}'.format(helptopic))


class HelpWindow(tkinter.Toplevel):
    """
    main help window

    Args:
        window(tkinter.Tk): the main window to spawn from
    """

    def __init__(self, window):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.helpbox = HelpTab(self)
        self.helpbox.pack()
