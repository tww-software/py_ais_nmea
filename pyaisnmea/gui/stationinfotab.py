"""
tab to display detailed info about an AIS station
"""

import logging
import os
import tkinter

import pyaisnmea.export as export


AISLOGGER = logging.getLogger(__name__)


class StationInfoTab(tkinter.ttk.Frame):
    """
    tab to provide detailed information on a single AIS Station

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    nostnerr = 'Please choose a station from the drop down to export data for.'

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
        self.stnlookup = {}
        self.stnoptions = tkinter.ttk.Combobox(self, width=55)
        self.stnoptions.pack(side='top')
        stnoptionsbutton = tkinter.Button(self, text='Display Info',
                                          command=self.show_stn_info)
        stnoptionsbutton.pack(side='top')
        lowerbuttons = tkinter.Frame(self)
        exportjsonbutton = tkinter.Button(lowerbuttons, text='JSON',
                                          command=self.export_json)
        exportjsonbutton.grid(column=0, row=0)
        exportkmzbutton = tkinter.Button(lowerbuttons, text='KMZ',
                                         command=self.export_kmz)
        exportkmzbutton.grid(column=1, row=0)
        exportcsvbutton = tkinter.Button(lowerbuttons, text='Positions CSV',
                                         command=self.export_positions_csv)
        exportcsvbutton.grid(column=2, row=0)
        exportdebugbutton = tkinter.Button(
            lowerbuttons, text='AIS Messages (DEBUG)',
            command=self.export_debug)
        exportdebugbutton.grid(column=3, row=0)
        lowerbuttons.pack(side='bottom')
        self.stntxt = tkinter.scrolledtext.ScrolledText(
            self, selectbackground='cyan')
        self.stntxt.pack(side='left', fill='both', expand=tkinter.TRUE)
        self.stntxt.bind('<Button-3>', self.select_all)
        self.stntxt.bind('<Control-c>', self.copy)
        self.stntxt.bind('<Control-C>', self.copy)
        self.stntxt.bind('<Control-a>', self.select_all)
        self.stntxt.bind('<Control-A>', self.select_all)

    def copy(self, event=None):
        """
        put highlighted text onto the clipboard when ctrl+c is used

        Args:
            event(tkinter.Event): event from the user (ctrl + c)
        """
        try:
            self.stntxt.clipboard_clear()
            self.stntxt.clipboard_append(self.stntxt.selection_get())
        except tkinter.TclError:
            pass

    def select_all(self, event=None):
        """
        select all the text in the textbox when ctrl+a is used

        Args:
            event(tkinter.Event): event from the user (ctrl + a)
        """
        self.stntxt.tag_add(tkinter.SEL, "1.0", tkinter.END)
        self.stntxt.mark_set(tkinter.INSERT, "1.0")
        self.stntxt.see(tkinter.INSERT)
        return 'break'

    def stn_options(self):
        """
        populate the stations to the station information tab drop down
        """
        for stn in self.tabs.window.aistracker.stations:
            stnobj = self.tabs.window.aistracker.stations[stn]
            dropdowntext = '{}  {}'.format(stnobj.mmsi, stnobj.name)
            self.stnlookup[dropdowntext] = stnobj.mmsi
        self.stnoptions['values'] = list(self.stnlookup.keys())

    def show_stn_info(self):
        """
        show individual station info
        """
        self.stntxt.delete(1.0, tkinter.END)
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                lookupmmsi = self.stnlookup[dropdowntext]
                stninfo = export.create_summary_text(
                    self.tabs.window.aistracker.stations[lookupmmsi]
                    .get_station_info())
                self.stntxt.insert(tkinter.INSERT, stninfo)
            except KeyError:
                tkinter.messagebox.showerror(
                    'Station Info', 'no data for MMSI - {}'.format(
                        dropdowntext))

    def export_kmz(self):
        """
        export KMZ for a single AIS station
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                outputfile = tkinter.filedialog.asksaveasfilename(
                    defaultextension=".kmz",
                    filetypes=(("keyhole markup language KMZ", "*.kmz"),
                               ("All Files", "*.*")))
                lookupmmsi = self.stnlookup[dropdowntext]
                self.tabs.window.aistracker.stations[lookupmmsi]. \
                    create_kml_map(outputfile, kmzoutput=True)
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                AISLOGGER.exception('export error')
                tkinter.messagebox.showerror(type(err).__name__, str(err))
        else:
            tkinter.messagebox.showerror('Export Files', self.nostnerr)

    def export_json(self):
        """
        export JSON for a single AIS station
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                outputfile = tkinter.filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=(("javascript object notation", "*.json"),
                               ("All Files", "*.*")))
                lookupmmsi = self.stnlookup[dropdowntext]
                stninfo = self.tabs.window.aistracker.stations[lookupmmsi]. \
                    get_station_info(verbose=True)
                export.write_json_file(stninfo, outputfile)
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                AISLOGGER.exception('export error')
                tkinter.messagebox.showerror(type(err).__name__, str(err))
        else:
            tkinter.messagebox.showerror('Export Files', self.nostnerr)

    def export_positions_csv(self):
        """
        export CSV for a single AIS station
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                outputfile = tkinter.filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=(("comma seperated values", "*.csv"),
                               ("All Files", "*.*")))
                lookupmmsi = self.stnlookup[dropdowntext]
                stninfo = self.tabs.window.aistracker.stations[lookupmmsi]
                stninfo.create_positions_csv(outputfile)
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                AISLOGGER.exception('export error')
                tkinter.messagebox.showerror(type(err).__name__, str(err))
        else:
            tkinter.messagebox.showerror('Export Files', self.nostnerr)

    def export_debug(self):
        """
        export all the AIS messages for a single AIS station
        pop open a file browser to allow the user to choose
        a directory to save the
        file and then save csv and jsonl to that location
        """
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                outpath = tkinter.filedialog.askdirectory()
                lookupmmsi = self.stnlookup[dropdowntext]
                jsonlines, messagecsvlist = \
                    self.tabs.window.messagelog.debug_output(
                        mmsi=lookupmmsi)
                export.write_json_lines(
                    jsonlines,
                    os.path.join(
                        outpath,
                        dropdowntext + '-ais-messages.jsonl'))
                export.write_csv_file(
                    messagecsvlist,
                    os.path.join(
                        outpath,
                        dropdowntext + '-ais-messages.csv'))
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                AISLOGGER.exception('export error')
                tkinter.messagebox.showerror(type(err).__name__, str(err))
        else:
            tkinter.messagebox.showerror('Export Files', self.nostnerr)
