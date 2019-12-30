"""
help windows and documentation for the AIS decoder GUI
"""

import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.ttk


LICENCE = """
MIT License

Copyright (c) 2019 Thomas W Whittam

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


EXPORT = """
This tab allows you to export all the data the AIS decoder currently has.

The export options are:

-ALL     - export all the file types below to a directory
-CSV     - Comma Seperated Values file containing similar data to the Ships tab
-TSV     - Tab Seperated Values file containing similar data to the Ships tab
-KML     - plain KML file with no custom icons (default icons will be used)
-KMZ     - Keyhole Markup Language Map with custom icons
-JSON    - JSON file containing stats and all the vessels with position reports
-GEOJSON - GEOJSON map of all AIS Station positions
-DEBUG   - outputs 2 files (CSV and JSON lines) output of all decoded messages

Data cannot be exported whilst the server is listening.
"""


MSGLOG = """
A table of all the AIS messages.

Double clicking a message will open a window with more detailed information
about that message.
"""


STNINFO = """
Display detailed information about an AIS Station and its last known location

KMZ maps of the vessels location and JSON data of all known positions can be
exported from here using the buttons at the bottom of the tab.
"""

class HelpTab(tkinter.ttk.Frame):
    """
    tab to provide a help description
    """

    help = {'Stats Tab': STATS,
            'Ships Tab': SHIPS,
            'Export Tab': EXPORT,
            'Message Log Tab': MSGLOG,
            'Station Information Tab': STNINFO,
            'Licence': LICENCE}

    def __init__(self, window):
        tkinter.ttk.Frame.__init__(self, window)
        self.helpoptions = tkinter.ttk.Combobox(self, state='readonly')
        self.helpoptions.pack(side='top')
        helpoptionsbutton = tkinter.Button(self, text='Display Info',
                                          command=self.show_help)
        helpoptionsbutton.pack(side='top')
        self.helptxt = tkinter.scrolledtext.ScrolledText(self)
        self.helptxt.pack(side='left', fill='both', expand=tkinter.TRUE)
        self.helpoptions['values'] = list(self.help.keys())
        self.helptxt.delete(1.0, tkinter.END)
        self.helptxt.insert(tkinter.INSERT, self.help['Licence'])

    def show_help(self):
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
    """

    def __init__(self, window):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.helpbox = HelpTab(self)
        self.helpbox.pack()
