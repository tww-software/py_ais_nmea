"""
A GUI for the AIS decoder written with tkinter
"""

import datetime
import sys
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.ttk
import queue
import multiprocessing
import threading
import logging
import os


import ais
import capturefile
import nmea
import network

AISLOGGER = logging.getLogger(__name__)


class BasicGUI():
    """
    a basic GUI using tkinter to control the program

    Note:
        tabs are numbered left to right

    Attributes:
        nmeatracker(): track the individual nmea sentences
        aistracker(): track the AIS messages and compute stats
        window(): the main window
        tab1
        tab2
        tab3
        txt
        exportoptions
    """

    def __init__(self):
        self.nmeatracker = nmea.NMEAtracker()
        self.aistracker = ais.AISTracker()
        self.window = tkinter.Tk()
        self.window.title('AIS NMEA 0183 Decoder')
        tabcontrol = tkinter.ttk.Notebook(self.window)
        self.tab1 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab1, text='Stats')
        self.tab2 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab2, text='Ships')
        self.tab3 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab3, text='Export')
        self.tab4 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab4, text='AIS Messages')
        self.tab5 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab5, text='NMEA Sentences')
        self.tab6 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab6, text='Station Information')
        self.exportoptions = tkinter.ttk.Combobox(self.tab3)
        self.stnoptions = tkinter.ttk.Combobox(self.tab6)
        self.stnoptions.grid(column=0, row=1)
        tabcontrol.pack(expand=1, fill='both')
        self.aisbox = tkinter.scrolledtext.ScrolledText(self.tab4)
        self.aisbox.pack(side='left', fill='both', expand=tkinter.TRUE)
        self.nmeabox = tkinter.scrolledtext.ScrolledText(self.tab5)
        self.nmeabox.pack(side='left', fill='both', expand=tkinter.TRUE)
        self.top_menu()
        self.mpq = multiprocessing.Queue()
        self.updateguithread = None
        self.serverprocess = None
        self.tree = tkinter.ttk.Treeview(self.tab2)
        verticalscrollbar = tkinter.ttk.Scrollbar(
            self.tab2, orient=tkinter.VERTICAL, command=self.tree.yview)
        verticalscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        horizontalscrollbar = tkinter.ttk.Scrollbar(
            self.tab2, orient=tkinter.HORIZONTAL, command=self.tree.xview)
        horizontalscrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        aismsgtotallabel = tkinter.Label(self.tab1, text='Total AIS messages')
        aismsgtotallabel.grid(column=0, row=0)
        self.aismsgtotal = tkinter.Label(self.tab1, text='')
        self.aismsgtotal.grid(column=1, row=0)
        nmeasentencetotallabel = tkinter.Label(self.tab1, text='Total NMEA sentences')
        nmeasentencetotallabel.grid(column=0, row=1)
        self.nmeasentencetotal = tkinter.Label(self.tab1, text='')
        self.nmeasentencetotal.grid(column=1, row=1)
        nmeamultipartassembledlabel = tkinter.Label(self.tab1, text='NMEA multipart sentences reassembled')
        nmeamultipartassembledlabel.grid(column=0, row=2)
        self.nmeamultipartassembled = tkinter.Label(self.tab1, text='')
        self.nmeamultipartassembled.grid(column=1, row=2)
        self.totalstnslabel = tkinter.Label(self.tab1, text='Total Unique Stations')
        self.totalstnslabel.grid(column=0, row=3)
        self.totalstns = tkinter.Label(self.tab1, text='')
        self.totalstns.grid(column=1, row=3)
        self.txt = tkinter.scrolledtext.ScrolledText(self.tab1)
        self.txt.grid(column=0, row=4)
        self.stntxt = tkinter.scrolledtext.ScrolledText(self.tab6)
        self.stntxt.grid(column=0, row=2)
        stnoptionsbutton = tkinter.Button(self.tab6, text='Display Info',
                                      command=self.show_stn_info)
        stnoptionsbutton.grid(column=1, row=1)
        self.serverrunning = False

    def top_menu(self):
        """
        format and add the top menu to the main window
        """
        menu = tkinter.Menu(self.window)
        openfileitem = tkinter.Menu(menu, tearoff=0)
        openfileitem.add_command(label='Open', command=self.open_file)
        openfileitem.add_command(label='Quit', command=self.quit)
        menu.add_cascade(label='File', menu=openfileitem)
        networkitem = tkinter.Menu(menu, tearoff=0)
        networkitem.add_command(label='Start Network Server', command=self.start_server)
        networkitem.add_command(label='Stop Network Server', command=self.stop_server)
        menu.add_cascade(label='Network', menu=networkitem)
        helpitem = tkinter.Menu(menu, tearoff=0)
        helpitem.add_command(label='Help', command=self.help)
        helpitem.add_command(label='About', command=self.about)
        menu.add_cascade(label='Help', menu=helpitem)
        self.window.config(menu=menu)

    def about(self):
        tkinter.messagebox.showinfo('About', 'Created by Thomas W Whittam')

    def help(self):
        tkinter.messagebox.showinfo('Help', 'No help for you')

    def start_server(self):
        self.serverrunning = True
        self.serverprocess = multiprocessing.Process(target=network.mpserver, args=[self.mpq])
        self.serverprocess.start()
        tkinter.messagebox.showinfo('Network', 'Server Started')
        self.updateguithread = threading.Thread(target=self.update)
        self.updateguithread.start()

    def stop_server(self):
        self.serverrunning = False
        mplock = multiprocessing.Lock()
        with mplock:
            self.mpq.put('stop')
        self.updateguithread.join()
        self.serverprocess.terminate()
        self.serverprocess = None
        self.updateguithread = None
        tkinter.messagebox.showinfo('Network', 'Server Stopped')
        self.export_options()

    def open_file(self):
        """
        pop open a file browser to allow the user to choose which NMEA 0183
        text file they want to process and then process it
        """
        inputfile = tkinter.filedialog.askopenfilename()
        self.aistracker, self.nmeatracker, _ = \
            capturefile.aistracker_from_file(inputfile, debug=True)
        self.export_options()
        self.stn_options()
        self.write_stats()
        self.write_stats_verbose()
        self.create_ship_table()

    def write_stats(self):
        """
        write the statistics from the ais and nmea trackers
        """
        self.aismsgtotal.configure(text=self.aistracker.messagesprocessed)
        self.nmeasentencetotal.configure(text=self.nmeatracker.sentencecount)
        self.nmeamultipartassembled.configure(text=self.nmeatracker.reassembled)
        self.totalstns.configure(text=self.aistracker.__len__())

    def write_stats_verbose(self):
        """
        give a bit more info
        """
        self.txt.delete(1.0, tkinter.END)
        printablestats = ais.create_summary_text(
            self.aistracker.tracker_stats())
        self.txt.insert(tkinter.INSERT, '\n\n')
        self.txt.insert(tkinter.INSERT, printablestats)

    def create_ship_table(self):
        """
        draw a large table in tab2 of all the AIS stations we have
        """
        self.tree.delete(*self.tree.get_children())
        tabledata = self.aistracker.create_table_data()
        headers = tabledata.pop(0)
        self.tree["columns"] = headers
        for column in headers:
            self.tree.column(column, width=200, minwidth=70, stretch=tkinter.NO)
            self.tree.heading(column, text=column, anchor=tkinter.W)
        counter = 0
        for line in tabledata:
            self.tree.insert('', counter, values=line)
            counter += 1
        self.tree.pack(side=tkinter.TOP, fill='both', expand=tkinter.TRUE)

    def export_csv(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("comma seperated values", "*.csv"),
                       ("All Files", "*.*")))
        tabledata = self.aistracker.create_table_data()
        ais.write_csv_file(tabledata, outputfile)

    def export_tsv(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".tsv",
            filetypes=(("tab seperated values", "*.tsv"),
                       ("All Files", "*.*")))
        tabledata = self.aistracker.create_table_data()
        ais.write_csv_file(tabledata, outputfile, dialect='excel-tab')

    def export_kml(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=(("keyhole markup language", "*.kml"),
                       ("All Files", "*.*")))
        self.aistracker.create_kml_map(outputfile, kmzoutput=False)

    def export_kmz(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".kmz",
            filetypes=(("keyhole markup language KMZ", "*.kmz"),
                       ("All Files", "*.*")))
        self.aistracker.create_kml_map(outputfile, kmzoutput=True)

    def export_json(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("javascript object notation", "*.json"),
                       ("All Files", "*.*")))
        joutdict = {}
        joutdict['NMEA Stats'] = self.nmeatracker.nmea_stats()
        joutdict['AIS Stats'] = self.aistracker.tracker_stats()
        joutdict['AIS Stations'] = self.aistracker.all_station_info()
        ais.write_json_file(joutdict, outputfile)

    def export_geojson(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".geojson",
            filetypes=(("geo json", "*.geojson"),
                       ("All Files", "*.*")))
        self.aistracker.create_geojson_map(outputfile)

    def export_all(self):
        """
        export all file formats
        """
        outpath = tkinter.filedialog.askdirectory()
        outputdata = self.aistracker.create_table_data()
        self.aistracker.create_kml_map(os.path.join(outpath, 'map.kmz'),
                                  kmzoutput=True)
        self.aistracker.create_kml_map(os.path.join(outpath, 'map.kml'),
                                  kmzoutput=False)
        ais.write_csv_file(outputdata,
                               os.path.join(outpath, 'vessel-data.tsv'),
                               dialect='excel-tab')
        ais.write_csv_file(outputdata,
                               os.path.join(outpath, 'vessel-data.csv'))
        self.aistracker.create_geojson_map(os.path.join(outpath, 'map.geojson'))
        joutdict = {}
        joutdict['NMEA Stats'] = self.nmeatracker.nmea_stats()
        joutdict['AIS Stats'] = self.aistracker.tracker_stats()
        joutdict['AIS Stations'] = self.aistracker.all_station_info()
        ais.write_json_file(joutdict,
                            os.path.join(outpath, 'vessel-data.json'))

    def export_options(self):
        """
        populate the export options drop down menu with file export options
        and add an export button next to it
        """
        self.exportoptions['values'] = ('ALL', 'CSV', 'TSV', 'KML',
                                        'KMZ', 'JSON', 'GEOJSON')
        self.exportoptions.set('KMZ')
        self.exportoptions.grid(column=1, row=1)
        exportbutton = tkinter.Button(self.tab3, text='Export',
                                      command=self.export_files)
        exportbutton.grid(column=2, row=1)
 
    def export_files(self):
        """
        choose which export command to run from the exportoptions drop down
        in the Export tab
        """
        commands = {'ALL': self.export_all,
                    'CSV': self.export_csv,
                    'TSV': self.export_tsv,
                    'KML': self.export_kml,
                    'KMZ': self.export_kmz,
                    'JSON': self.export_json,
                    'GEOJSON': self.export_geojson}
        option = self.exportoptions.get()
        commands[option]()

    def stn_options(self):
        """
        populate the stations to the station information tab drop down
        """
        self.stnoptions['values'] = list(self.aistracker.stations.keys())

    def show_stn_info(self):
        """
        show individual station info
        """
        self.stntxt.delete(1.0, tkinter.END)
        lookupmmsi = self.stnoptions.get()
        if lookupmmsi != '':
            stninfo = ais.create_summary_text(self.aistracker.stations[lookupmmsi].get_station_info())
            self.stntxt.insert(tkinter.INSERT, stninfo)

    def update(self):
        while True:
            qdata = self.mpq.get()
            if qdata:
                if qdata == 'stop':
                    break
                try:
                    data = qdata.decode('utf-8')
                    self.nmeabox.insert(tkinter.INSERT, data)
                    self.nmeabox.see(tkinter.END)
                    payload = self.nmeatracker.process_sentence(data)
                    if payload:
                        currenttime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        msg = self.aistracker.process_message(payload, timestamp=currenttime)
                        self.aisbox.insert(tkinter.INSERT, msg.__str__())
                        self.aisbox.insert(tkinter.INSERT, '\n\n')
                        self.aisbox.see(tkinter.END)
                        self.write_stats()
                        if currenttime.endswith('5'):
                            self.create_ship_table()
                            self.write_stats_verbose()
                            self.stn_options()
                            self.show_stn_info()
                except (nmea.NMEAInvalidSentence, nmea.NMEACheckSumFailed,
                        ais.UnknownMessageType, ais.InvalidMMSI) as err:
                    AISLOGGER.debug(str(err))
                    continue
                except IndexError:
                    AISLOGGER.debug('no data on line')
                    continue

    def display_gui(self):
        """
        start the GUI main loop
        """
        self.window.mainloop()

    def quit(self):
        """
        open a confirmation box asking if the user wants to quit if yes then
        exit the program with exit code of 0
        """
        res = tkinter.messagebox.askyesno('Exiting Program', 'Are you sure?')
        if res:
            if self.serverrunning:
                self.stop_server()
            sys.exit(0)


if __name__ == '__main__':
    AISGUI = BasicGUI()
    AISGUI.display_gui()
