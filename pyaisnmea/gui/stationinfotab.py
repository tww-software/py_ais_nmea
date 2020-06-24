"""
tab to display detailed info about an AIS station
"""

import tkinter

import pyaisnmea.ais as ais


class StationInfoTab(tkinter.ttk.Frame):
    """
    tab to provide detailed information on a single AIS Station

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

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
        exportcsvbutton = tkinter.Button(lowerbuttons, text='CSV',
                                         command=self.export_csv)
        exportcsvbutton.grid(column=2, row=0)
        lowerbuttons.pack(side='bottom')
        self.stntxt = tkinter.scrolledtext.ScrolledText(
            self, selectbackground='cyan')
        self.stntxt.pack(side='left', fill='both', expand=tkinter.TRUE)
        self.stntxt.bind('<Button-3>', self.select_all)
        self.stntxt.bind('<Control-c>', self.copy)
        self.stntxt.bind('<Control-C>', self.copy)
        self.stntxt.bind('<Control-a>', self.select_all)
        self.stntxt.bind('<Control-A>', self.select_all)

    def copy(self, event):
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

    def select_all(self, event):
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
                stninfo = ais.create_summary_text(
                    self.tabs.window.aistracker.stations[lookupmmsi]
                    .get_station_info())
                self.stntxt.insert(tkinter.INSERT, stninfo)
            except KeyError:
                tkinter.messagebox.showerror(
                    'Station Info', 'no data for MMSI - {}'.format(lookupmmsi))

    def export_kmz(self):
        """
        export KMZ for a single AIS station
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".kmz",
            filetypes=(("keyhole markup language KMZ", "*.kmz"),
                       ("All Files", "*.*")))
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                lookupmmsi = self.stnlookup[dropdowntext]
                self.tabs.window.aistracker.stations[lookupmmsi]. \
                    create_kml_map(outputfile, kmzoutput=True)
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                tkinter.messagebox.showerror('Export Files', str(err))

    def export_json(self):
        """
        export JSON for a single AIS station
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("javascript object notation", "*.json"),
                       ("All Files", "*.*")))
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                lookupmmsi = self.stnlookup[dropdowntext]
                stninfo = self.tabs.window.aistracker.stations[lookupmmsi]. \
                    get_station_info(verbose=True)
                ais.write_json_file(stninfo, outputfile)
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                tkinter.messagebox.showerror('Export Files', str(err))

    def export_csv(self):
        """
        export CSV for a single AIS station
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("comma seperated values", "*.csv"),
                       ("All Files", "*.*")))
        dropdowntext = self.stnoptions.get()
        if dropdowntext != '':
            try:
                lookupmmsi = self.stnlookup[dropdowntext]
                stninfo = self.tabs.window.aistracker.stations[lookupmmsi]
                stninfo.create_positions_csv(outputfile)
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                tkinter.messagebox.showerror('Export Files', str(err))
