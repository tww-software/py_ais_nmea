"""
A GUI for the AIS decoder written with tkinter
"""

import datetime
import logging
import multiprocessing
import os
import threading
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.ttk

import ais
import capturefile
import nmea
import network

AISLOGGER = logging.getLogger(__name__)


class StatsTab(tkinter.ttk.Frame):
    """
    provide overall statistics for all the AIS Stations we can see
    """

    def __init__(self, tc):
        tkinter.ttk.Frame.__init__(self, tc)
        self.tc = tc
        aismsgtotallabel = tkinter.Label(self, text='Total AIS messages')
        aismsgtotallabel.grid(column=0, row=0)
        self.aismsgtotal = tkinter.Label(self, text='')
        self.aismsgtotal.grid(column=1, row=0)
        nmeasentencetotallabel = tkinter.Label(
            self, text='Total NMEA sentences')
        nmeasentencetotallabel.grid(column=0, row=1)
        self.nmeasentencetotal = tkinter.Label(self, text='')
        self.nmeasentencetotal.grid(column=1, row=1)
        nmeamultipartassembledlabel = tkinter.Label(
            self, text='NMEA multipart sentences reassembled')
        nmeamultipartassembledlabel.grid(column=0, row=2)
        self.nmeamultipartassembled = tkinter.Label(self, text='')
        self.nmeamultipartassembled.grid(column=1, row=2)
        self.totalstnslabel = tkinter.Label(
            self, text='Total Unique Stations')
        self.totalstnslabel.grid(column=0, row=3)
        self.totalstns = tkinter.Label(self, text='')
        self.totalstns.grid(column=1, row=3)
        self.msgstatstxt = tkinter.scrolledtext.ScrolledText(self)
        self.msgstatstxt.configure(width=50)
        self.msgstatstxt.grid(column=0, row=4)
        self.shiptypestxt = tkinter.scrolledtext.ScrolledText(self)
        self.shiptypestxt.configure(width=50)
        self.shiptypestxt.grid(column=1, row=4)
        self.stntypestxt = tkinter.scrolledtext.ScrolledText(self)
        self.stntypestxt.configure(width=30)
        self.stntypestxt.grid(column=2, row=4)
        self.flagstxt = tkinter.scrolledtext.ScrolledText(self)
        self.flagstxt.configure(width=30)
        self.flagstxt.grid(column=3, row=4)

    def write_stats(self):
        """
        write the statistics from the ais and nmea trackers
        """
        self.aismsgtotal.configure(
            text=self.tc.window.aistracker.messagesprocessed)
        self.nmeasentencetotal.configure(
            text=self.tc.window.nmeatracker.sentencecount)
        self.nmeamultipartassembled.configure(
            text=self.tc.window.nmeatracker.reassembled)
        self.totalstns.configure(text=self.tc.window.aistracker.__len__())

    def write_stats_verbose(self):
        """
        give a bit more info than write_stats
        """
        self.msgstatstxt.delete(1.0, tkinter.END)
        self.shiptypestxt.delete(1.0, tkinter.END)
        self.flagstxt.delete(1.0, tkinter.END)
        self.stntypestxt.delete(1.0, tkinter.END)
        stats = self.tc.window.aistracker.tracker_stats()
        self.msgstatstxt.insert(
            tkinter.INSERT,
            ais.create_summary_text(stats['Message Stats']))
        self.shiptypestxt.insert(
            tkinter.INSERT,
            ais.create_summary_text(stats['Ship Types']))
        self.stntypestxt.insert(
            tkinter.INSERT,
            ais.create_summary_text(stats['AIS Station Types']))
        self.flagstxt.insert(
            tkinter.INSERT,
            ais.create_summary_text(stats['Country Flags']))


class ShipsTableTab(tkinter.ttk.Frame):
    """
    tab to display a table of all the AIS Stations we have
    """

    def __init__(self, tc):
        tkinter.ttk.Frame.__init__(self, tc)
        self.tc = tc
        self.tree = tkinter.ttk.Treeview(self)
        verticalscrollbar = tkinter.ttk.Scrollbar(
            self, orient=tkinter.VERTICAL, command=self.tree.yview)
        verticalscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        horizontalscrollbar = tkinter.ttk.Scrollbar(
            self, orient=tkinter.HORIZONTAL, command=self.tree.xview)
        horizontalscrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.tree.bind("<Double-1>", self.on_tree_item_doubleclick)
        self.tree.configure(yscrollcommand=verticalscrollbar.set,
                            xscrollcommand=horizontalscrollbar.set)



    def on_tree_item_doubleclick(self, event):
        """
        if the user double clicks on a row in the tree
        grab the MMSI of that row and switch to the station information tab
        (tab6) and display more detailed info
        """
        item = self.tree.identify('item', event.x, event.y)
        clickedmmsi = self.tree.item(item)['values'][0]
        self.tc.tab6.stnoptions.set(clickedmmsi)
        self.tc.tab6.show_stn_info()
        self.tc.select(self.tc.tab6)

    def create_ship_table(self):
        """
        draw a large table in tab2 of all the AIS stations we have
        """
        self.tree.delete(*self.tree.get_children())
        tabledata = self.tc.window.aistracker.create_table_data()
        headers = tabledata.pop(0)
        self.tree["columns"] = headers
        for column in headers:
            self.tree.column(column, width=200, minwidth=70,
                             stretch=tkinter.YES)
            self.tree.heading(column, text=column, anchor=tkinter.W)
        counter = 0
        for line in tabledata:
            self.tree.insert('', counter, values=line)
            counter += 1
        self.tree.pack(side=tkinter.TOP, fill='both', expand=tkinter.TRUE)
        self.tree['show'] = 'headings'


class ExportTab(tkinter.ttk.Frame):
    """
    the tab in the main window that contains the export file options
    """

    def __init__(self, tc):
        tkinter.ttk.Frame.__init__(self, tc)
        self.tc = tc
        self.exportoptions = tkinter.ttk.Combobox(self)
        self.export_options()

    def export_options(self):
        """
        populate the export options drop down menu with file export options
        and add an export button next to it
        """
        self.exportoptions['values'] = ('ALL', 'CSV', 'TSV', 'KML',
                                        'KMZ', 'JSON', 'GEOJSON', 'DEBUG')
        self.exportoptions.set('KMZ')
        self.exportoptions.grid(column=1, row=1)
        exportbutton = tkinter.Button(self, text='Export',
                                      command=self.export_files)
        exportbutton.grid(column=2, row=1)

    def export_files(self):
        """
        choose which export command to run from the exportoptions drop down
        in the Export tab
        """
        if self.tc.window.serverrunning:
            tkinter.messagebox.showwarning(
                'WARNING', 'Cannot export files whilst server is running')
        else:
            commands = {'ALL': self.export_all,
                        'CSV': self.export_csv,
                        'TSV': self.export_tsv,
                        'KML': self.export_kml,
                        'KMZ': self.export_kmz,
                        'JSON': self.export_json,
                        'GEOJSON': self.export_geojson,
                        'DEBUG': self.export_debug}
            option = self.exportoptions.get()
            commands[option]()
            tkinter.messagebox.showinfo('Export Files', 'Export Successful')

    def export_csv(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("comma seperated values", "*.csv"),
                       ("All Files", "*.*")))
        tabledata = self.tc.window.aistracker.create_table_data()
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
        tabledata = self.tc.window.aistracker.create_table_data()
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
        self.tc.window.aistracker.create_kml_map(outputfile, kmzoutput=False)

    def export_kmz(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".kmz",
            filetypes=(("keyhole markup language KMZ", "*.kmz"),
                       ("All Files", "*.*")))
        self.tc.window.aistracker.create_kml_map(outputfile, kmzoutput=True)

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
        joutdict['NMEA Stats'] = self.tc.window.nmeatracker.nmea_stats()
        joutdict['AIS Stats'] = self.tc.window.aistracker.tracker_stats()
        joutdict['AIS Stations'] = self.tc.window.aistracker.all_station_info()
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
        self.tc.window.aistracker.create_geojson_map(outputfile)

    def export_debug(self, outpath=None):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        if not outpath:
            outpath = tkinter.filedialog.askdirectory()
        ais.write_json_lines(self.tc.window.messagelist,
                             os.path.join(outpath,
                                          'ais-messages.jsonl'))
        messagecsvlist = capturefile.message_debug_csv_table(
            self.tc.window.messagelist)
        ais.write_csv_file(messagecsvlist,
                           os.path.join(outpath, 'ais-messages.csv'))

    def export_all(self):
        """
        export all file formats
        """
        outpath = tkinter.filedialog.askdirectory()
        outputdata = self.tc.window.aistracker.create_table_data()
        self.tc.window.aistracker.create_kml_map(
            os.path.join(outpath, 'map.kmz'),
            kmzoutput=True)
        self.tc.window.aistracker.create_kml_map(
            os.path.join(outpath, 'map.kml'),
            kmzoutput=False)
        ais.write_csv_file(outputdata,
                           os.path.join(outpath, 'vessel-data.tsv'),
                           dialect='excel-tab')
        ais.write_csv_file(outputdata,
                           os.path.join(outpath, 'vessel-data.csv'))
        self.tc.window.aistracker.create_geojson_map(
            os.path.join(outpath, 'map.geojson'))
        joutdict = {}
        joutdict['NMEA Stats'] = self.tc.window.nmeatracker.nmea_stats()
        joutdict['AIS Stats'] = self.tc.window.aistracker.tracker_stats()
        joutdict['AIS Stations'] = self.tc.window.aistracker.all_station_info()
        ais.write_json_file(joutdict,
                            os.path.join(outpath, 'vessel-data.json'))
        self.export_debug(outpath)


class TextBoxTab(tkinter.ttk.Frame):
    """
    tab to display all the AIS messages or NMEA Sentences

    Note:
        basically a tab with a big text box on it that autoscrolls as you
        update it
    """

    def __init__(self, tc):
        tkinter.ttk.Frame.__init__(self, tc)
        self.tc = tc
        self.aisbox = tkinter.scrolledtext.ScrolledText(self)
        self.aisbox.pack(side='left', fill='both', expand=tkinter.TRUE)

    def append_text(self, text):
        self.aisbox.insert(tkinter.INSERT, text)
        self.aisbox.insert(tkinter.INSERT, '\n')
        self.aisbox.see(tkinter.END)


class StationInfoTab(tkinter.ttk.Frame):
    """
    tab to provide detailed information on a single AIS Station
    """

    def __init__(self, tc):
        tkinter.ttk.Frame.__init__(self, tc)
        self.tc = tc
        self.stnoptions = tkinter.ttk.Combobox(self)
        self.stnoptions.pack(side='top')
        stnoptionsbutton = tkinter.Button(self, text='Display Info',
                                          command=self.show_stn_info)
        stnoptionsbutton.pack(side='top')
        self.stntxt = tkinter.scrolledtext.ScrolledText(self)
        self.stntxt.pack(side='left', fill='both', expand=tkinter.TRUE)

    def stn_options(self):
        """
        populate the stations to the station information tab drop down
        """
        self.stnoptions['values'] = list(
            self.tc.window.aistracker.stations.keys())

    def show_stn_info(self):
        """
        show individual station info
        """
        self.stntxt.delete(1.0, tkinter.END)
        lookupmmsi = self.stnoptions.get()
        if lookupmmsi != '':
            stninfo = ais.create_summary_text(
                self.tc.window.aistracker.stations[lookupmmsi]
                .get_station_info())
            self.stntxt.insert(tkinter.INSERT, stninfo)


class TabControl(tkinter.ttk.Notebook):
    """
    organise the main tabs

    Note:
        tabs are numbered left to right
    """

    def __init__(self, window):
        tkinter.ttk.Notebook.__init__(self, window)
        self.window = window
        self.tab1 = StatsTab(self)
        self.add(self.tab1, text='Stats')
        self.tab2 = ShipsTableTab(self)
        self.add(self.tab2, text='Ships')
        self.tab3 = ExportTab(self)
        self.add(self.tab3, text='Export')
        self.tab4 = TextBoxTab(self)
        self.add(self.tab4, text='AIS Messages')
        self.tab5 = TextBoxTab(self)
        self.add(self.tab5, text='NMEA Sentences')
        self.tab6 = StationInfoTab(self)
        self.add(self.tab6, text='Station Information')


class BasicGUI(tkinter.Tk):
    """
    a basic GUI using tkinter to control the program

    Attributes:

    """

    def __init__(self):
        tkinter.Tk.__init__(self)
        self.nmeatracker = nmea.NMEAtracker()
        self.aistracker = ais.AISTracker()
        self.messagelist = []
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.title('AIS NMEA 0183 Decoder')
        self.statuslabel = tkinter.Label(self, text='', bg='light grey')
        self.statuslabel.pack(fill=tkinter.X)
        self.tabcontrol = TabControl(self)
        self.tabcontrol.pack(expand=1, fill='both')
        self.top_menu()
        self.mpq = multiprocessing.Queue()
        self.updateguithread = None
        self.serverprocess = None
        self.serverrunning = False

    def top_menu(self):
        """
        format and add the top menu to the main window
        """
        menu = tkinter.Menu(self)
        openfileitem = tkinter.Menu(menu, tearoff=0)
        openfileitem.add_command(label='Open', command=self.open_file)
        openfileitem.add_command(label='Quit', command=self.quit)
        menu.add_cascade(label='File', menu=openfileitem)
        networkitem = tkinter.Menu(menu, tearoff=0)
        networkitem.add_command(
            label='Start Network Server', command=self.start_server)
        networkitem.add_command(
            label='Stop Network Server', command=self.stop_server)
        menu.add_cascade(label='Network', menu=networkitem)
        helpitem = tkinter.Menu(menu, tearoff=0)
        helpitem.add_command(label='Help', command=self.help)
        helpitem.add_command(label='About', command=self.about)
        menu.add_cascade(label='Help', menu=helpitem)
        self.config(menu=menu)

    @staticmethod
    def about():
        """
        display version, licence and who created it
        """
        tkinter.messagebox.showinfo('About', 'Created by Thomas W Whittam')

    def help(self):
        """
        display the help window
        """
        tkinter.messagebox.showinfo('Help', 'No help for you')

    def start_server(self):
        """
        start the server
        """
        self.serverrunning = True
        self.serverprocess = multiprocessing.Process(
            target=network.mpserver, args=[self.mpq])
        self.serverprocess.start()
        tkinter.messagebox.showinfo('Network', 'Server Started')
        self.updateguithread = threading.Thread(target=self.update)
        self.updateguithread.start()
        self.statuslabel.config(text='AIS Server Listening',
                                fg='black', bg='green2')

    def stop_server(self):
        """
        stop the server
        """
        self.serverrunning = False
        mplock = multiprocessing.Lock()
        with mplock:
            self.mpq.put('stop')
        self.updateguithread.join()
        self.serverprocess.terminate()
        self.serverprocess = None
        self.updateguithread = None
        tkinter.messagebox.showinfo('Network', 'Server Stopped')
        self.statuslabel.config(text='', bg='light grey')

    def open_file(self):
        """
        pop open a file browser to allow the user to choose which NMEA 0183
        text file they want to process and then process it
        """
        if self.serverrunning:
            tkinter.messagebox.showwarning(
                'WARNING', 'Stop Server First')
        else:
            inputfile = tkinter.filedialog.askopenfilename()
            self.aistracker, self.nmeatracker, self.messagelist = \
                capturefile.aistracker_from_file(inputfile, debug=True)
            self.tabcontrol.tab6.stn_options()
            self.tabcontrol.tab1.write_stats()
            self.tabcontrol.tab1.write_stats_verbose()
            self.tabcontrol.tab2.create_ship_table()
            for message in self.messagelist:
                self.tabcontrol.tab4.append_text(
                    message['Detailed Description'])
                self.tabcontrol.tab5.append_text(message['NMEA Payload'])
            self.statuslabel.config(
                text='Loaded capture file - {}'.format(inputfile),
                fg='black', bg='light grey')

    def update(self):
        """
        update the GUI in another thread whist the server is running and
        recieving packets
        """
        while True:
            qdata = self.mpq.get()
            if qdata:
                if qdata == 'stop':
                    break
                try:
                    self.tabcontrol.tab5.append_text(qdata)
                    payload = self.nmeatracker.process_sentence(qdata)
                    if payload:
                        currenttime = datetime.datetime.utcnow().strftime(
                            '%Y/%m/%d %H:%M:%S')
                        msg = self.aistracker.process_message(
                            payload, timestamp=currenttime)
                        decodedmsg = {}
                        decodedmsg['NMEA Payload'] = payload
                        decodedmsg['MMSI'] = msg.mmsi
                        decodedmsg['Message Type Number'] = msg.msgtype
                        decodedmsg['Detailed Description'] = msg.__str__()
                        decodedmsg['Time'] = currenttime
                        self.messagelist.append(decodedmsg)
                        self.tabcontrol.tab4.append_text(msg.__str__())
                        self.tabcontrol.tab1.write_stats()
                        if currenttime.endswith('5'):
                            self.tabcontrol.tab2.create_ship_table()
                            self.tabcontrol.tab1.write_stats_verbose()
                            self.tabcontrol.tab6.stn_options()
                            self.tabcontrol.tab6.show_stn_info()
                except (nmea.NMEAInvalidSentence, nmea.NMEACheckSumFailed,
                        ais.UnknownMessageType, ais.InvalidMMSI) as err:
                    AISLOGGER.debug(str(err))
                    continue
                except IndexError:
                    AISLOGGER.debug('no data on line')
                    continue

    def quit(self):
        """
        open a confirmation box asking if the user wants to quit if yes then
        exit the program with exit code of 0
        """
        res = tkinter.messagebox.askyesno('Exiting Program', 'Are you sure?')
        if res:
            if self.serverrunning:
                self.stop_server()
            self.destroy()


if __name__ == '__main__':
    AISGUI = BasicGUI()
    AISGUI.mainloop()
