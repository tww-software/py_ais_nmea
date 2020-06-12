"""
A GUI for the AIS decoder written with tkinter
"""

import datetime
import logging
import multiprocessing
import os
import threading
import time
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.ttk

import pyaisnmea.ais as ais
import pyaisnmea.capturefile as capturefile
import pyaisnmea.guihelp as guihelp
import pyaisnmea.livekmlmap as livekmlmap
import pyaisnmea.nmea as nmea
import pyaisnmea.network as network

AISLOGGER = logging.getLogger(__name__)


class StatsTab(tkinter.ttk.Frame):
    """
    provide overall statistics for all the AIS Stations we can see

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
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
        totalstnslabel = tkinter.Label(
            self, text='Total Unique Stations')
        totalstnslabel.grid(column=0, row=3)
        self.totalstns = tkinter.Label(self, text='')
        self.totalstns.grid(column=1, row=3)
        starttimelabel = tkinter.Label(self, text='Start Time')
        starttimelabel.grid(column=0, row=4)
        self.starttime = tkinter.Label(self, text='')
        self.starttime.grid(column=1, row=4)
        latesttimelabel = tkinter.Label(self, text='Latest Time')
        latesttimelabel.grid(column=0, row=5)
        self.latesttime = tkinter.Label(self, text='')
        self.latesttime.grid(column=1, row=5)
        self.msgstatstxt = tkinter.scrolledtext.ScrolledText(self)
        self.msgstatstxt.configure(width=60)
        self.msgstatstxt.grid(column=0, row=6)
        self.shiptypestxt = tkinter.scrolledtext.ScrolledText(self)
        self.shiptypestxt.configure(width=60)
        self.shiptypestxt.grid(column=1, row=6)
        self.flagstxt = tkinter.scrolledtext.ScrolledText(self)
        self.flagstxt.configure(width=40)
        self.flagstxt.grid(column=2, row=6)

    def write_stats(self):
        """
        write the statistics from the ais and nmea trackers
        """
        self.aismsgtotal.configure(
            text=self.tabs.window.aistracker.messagesprocessed)
        self.nmeasentencetotal.configure(
            text=self.tabs.window.nmeatracker.sentencecount)
        self.nmeamultipartassembled.configure(
            text=self.tabs.window.nmeatracker.reassembled)
        self.totalstns.configure(text=self.tabs.window.aistracker.__len__())
        try:
            self.latesttime.configure(
                text=self.tabs.window.aistracker.timings[
                    len(self.tabs.window.aistracker.timings) - 1])
        except IndexError:
            self.latesttime.configure(text='Unavailable')

    def write_stats_verbose(self):
        """
        give a bit more info than write_stats
        """
        self.msgstatstxt.delete(1.0, tkinter.END)
        self.shiptypestxt.delete(1.0, tkinter.END)
        self.flagstxt.delete(1.0, tkinter.END)
        stats = self.tabs.window.aistracker.tracker_stats()
        self.msgstatstxt.insert(
            tkinter.INSERT,
            ais.create_summary_text(stats['Message Stats']))
        self.shiptypestxt.insert(
            tkinter.INSERT,
            ais.create_summary_text(stats['Ship Types']))
        self.flagstxt.insert(
            tkinter.INSERT,
            ais.create_summary_text(stats['Country Flags']))


class ShipsTableTab(tkinter.ttk.Frame):
    """
    tab to display a table of all the AIS Stations we have

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
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
        (stninfotab) and display more detailed info
        """
        item = self.tree.identify('item', event.x, event.y)
        clickedmmsi = str(self.tree.item(item)['values'][0])
        if len(clickedmmsi) == 7:
            clickedmmsi = '00' + clickedmmsi
        self.tabs.stninfotab.stnoptions.set(clickedmmsi)
        self.tabs.stninfotab.show_stn_info()
        self.tabs.select(self.tabs.stninfotab)

    def create_ship_table(self):
        """
        draw a large table in shipstab of all the AIS stations we have
        """
        self.tree.delete(*self.tree.get_children())
        tabledata = self.tabs.window.aistracker.create_nav_table()
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

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
        self.exportoptions = tkinter.ttk.Combobox(self, state='readonly')
        self.export_options()

    def export_options(self):
        """
        populate the export options drop down menu with file export options
        and add an export button next to it
        """
        self.exportoptions['values'] = ('OVERVIEW', 'CSV', 'TSV', 'KML',
                                        'KMZ', 'JSON', 'VERBOSE JSON',
                                        'GEOJSON', 'DEBUG')
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
        if self.tabs.window.serverrunning:
            tkinter.messagebox.showwarning(
                'WARNING', 'Cannot export files whilst server is running')
        else:
            commands = {'OVERVIEW': self.export_overview,
                        'CSV': self.export_csv,
                        'TSV': self.export_tsv,
                        'KML': self.export_kml,
                        'KMZ': self.export_kmz,
                        'JSON': self.export_json,
                        'VERBOSE JSON': self.export_verbose_json,
                        'GEOJSON': self.export_geojson,
                        'DEBUG': self.export_debug}
            option = self.exportoptions.get()
            try:
                commands[option]()
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                AISLOGGER.exception('export error')
                tkinter.messagebox.showerror('Export Files', str(err))

    def export_csv(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("comma seperated values", "*.csv"),
                       ("All Files", "*.*")))
        tabledata = self.tabs.window.aistracker.create_table_data()
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
        tabledata = self.tabs.window.aistracker.create_table_data()
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
        self.tabs.window.aistracker.create_kml_map(outputfile, kmzoutput=False)

    def export_kmz(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".kmz",
            filetypes=(("keyhole markup language KMZ", "*.kmz"),
                       ("All Files", "*.*")))
        self.tabs.window.aistracker.create_kml_map(outputfile, kmzoutput=True)

    def export_json(self, verbosejson=False):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("javascript object notation", "*.json"),
                       ("All Files", "*.*")))
        joutdict = {}
        joutdict['NMEA Stats'] = self.tabs.window.nmeatracker.nmea_stats()
        joutdict['AIS Stats'] = self.tabs.window.aistracker.tracker_stats()
        joutdict['AIS Stations'] = self.tabs.window.aistracker. \
            all_station_info(verbose=verbosejson)
        ais.write_json_file(joutdict, outputfile)

    def export_verbose_json(self):
        """
        json file with all postion reports for each vessel
        """
        self.export_json(verbosejson=True)

    def export_geojson(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".geojson",
            filetypes=(("geo json", "*.geojson"),
                       ("All Files", "*.*")))
        self.tabs.window.aistracker.create_geojson_map(outputfile)

    def export_debug(self, outpath=None):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        if not outpath:
            outpath = tkinter.filedialog.askdirectory()
        jsonlines, messagecsvlist = capturefile.debug_output(
            self.tabs.window.messagedict)
        ais.write_json_lines(jsonlines,
                             os.path.join(outpath,
                                          'ais-messages.jsonl'))
        ais.write_csv_file(messagecsvlist,
                           os.path.join(outpath, 'ais-messages.csv'))

    def export_overview(self):
        """
        export the most popular file formats
        KMZ - map
        JSON & CSV - vessel details
        JSONLINES and CSV - message debug
        """
        outpath = tkinter.filedialog.askdirectory()
        outputdata = self.tabs.window.aistracker.create_table_data()
        self.tabs.window.aistracker.create_kml_map(
            os.path.join(outpath, 'map.kmz'),
            kmzoutput=True)
        ais.write_csv_file(outputdata,
                           os.path.join(outpath, 'vessel-data.csv'))
        joutdict = {}
        joutdict['NMEA Stats'] = self.tabs.window.nmeatracker.nmea_stats()
        joutdict['AIS Stats'] = self.tabs.window.aistracker.tracker_stats()
        joutdict['AIS Stations'] = self.tabs.window.aistracker. \
            all_station_info(verbose=False)
        ais.write_json_file(joutdict,
                            os.path.join(outpath, 'vessel-data.json'))
        self.export_debug(outpath)


class AISMessageTab(tkinter.ttk.Frame):
    """
    tab to display all the NMEA Sentences and descriptions + times

    Note:
        basically a tab with a table inside

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
        self.counter = 0
        self.tree = tkinter.ttk.Treeview(self)
        verticalscrollbar = tkinter.ttk.Scrollbar(
            self, orient=tkinter.VERTICAL, command=self.tree.yview)
        verticalscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        horizontalscrollbar = tkinter.ttk.Scrollbar(
            self, orient=tkinter.HORIZONTAL, command=self.tree.xview)
        horizontalscrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.tree.configure(yscrollcommand=verticalscrollbar.set,
                            xscrollcommand=horizontalscrollbar.set)
        self.create_message_table()
        self.tree.bind("<Double-1>", self.on_tree_item_doubleclick)

    def on_tree_item_doubleclick(self, event):
        """
        open a message box with further details when a user double clicks a
        message
        """
        item = self.tree.identify('item', event.x, event.y)
        clickednmea = self.tree.item(item)['values'][0]
        messagewindow = MessageWindow(self.tabs.window)
        msgsummary = ais.create_summary_text(
            self.tabs.window.messagedict[clickednmea].__dict__)
        messagewindow.msgdetailsbox.append_text(msgsummary)

    def create_message_table(self):
        """
        draw a large table in messagetab of all the NMEA sentences we have
        """
        self.tree.delete(*self.tree.get_children())
        headers = ['NMEA', 'AIS', 'MMSI', 'Timestamp']
        self.tree["columns"] = headers
        for column in headers:
            self.tree.column(column, width=200, minwidth=70,
                             stretch=tkinter.YES)
            self.tree.heading(column, text=column, anchor=tkinter.W)
        self.tree.pack(side=tkinter.TOP, fill='both', expand=tkinter.TRUE)
        self.tree['show'] = 'headings'

    def add_new_line(self, line):
        """
        add a new line to the tree table and scroll down to it
        """
        self.tree.insert('', self.counter, values=line)
        self.counter += 1
        self.tree.yview_moveto(1)


class TextBoxTab(tkinter.ttk.Frame):
    """
    tab to display all the AIS messages or NMEA Sentences

    Note:
        basically a tab with a big text box on it that autoscrolls as you
        update it

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
        self.aisbox = tkinter.scrolledtext.ScrolledText(self)
        self.aisbox.pack(side='left', fill='both', expand=tkinter.TRUE)

    def append_text(self, text):
        """
        write text into the box and append a newline after it

        Args:
            text(str): text to write in the box
        """
        self.aisbox.insert(tkinter.INSERT, text)
        self.aisbox.insert(tkinter.INSERT, '\n\n')
        self.aisbox.see(tkinter.END)


class StationInfoTab(tkinter.ttk.Frame):
    """
    tab to provide detailed information on a single AIS Station

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
        self.stnoptions = tkinter.ttk.Combobox(self)
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
        self.stntxt = tkinter.scrolledtext.ScrolledText(self)
        self.stntxt.pack(side='left', fill='both', expand=tkinter.TRUE)

    def stn_options(self):
        """
        populate the stations to the station information tab drop down
        """
        self.stnoptions['values'] = list(
            self.tabs.window.aistracker.stations.keys())

    def show_stn_info(self):
        """
        show individual station info
        """
        self.stntxt.delete(1.0, tkinter.END)
        lookupmmsi = self.stnoptions.get()
        if lookupmmsi != '':
            try:
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
        lookupmmsi = self.stnoptions.get()
        if lookupmmsi != '':
            try:
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
        lookupmmsi = self.stnoptions.get()
        if lookupmmsi != '':
            try:
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
        lookupmmsi = self.stnoptions.get()
        if lookupmmsi != '':
            try:
                stninfo = self.tabs.window.aistracker.stations[lookupmmsi]
                stninfo.create_positions_csv(outputfile)
                tkinter.messagebox.showinfo(
                    'Export Files', 'Export Successful')
            except Exception as err:
                tkinter.messagebox.showerror('Export Files', str(err))

class TabControl(tkinter.ttk.Notebook):
    """
    organise the main tabs

    Note:
        tabs are numbered left to right

    Args:
        window(tkinter.Tk): the main window this spawns from
    """

    def __init__(self, window):
        tkinter.ttk.Notebook.__init__(self, window)
        self.window = window
        self.statstab = StatsTab(self)
        self.add(self.statstab, text='Stats')
        self.shipstab = ShipsTableTab(self)
        self.add(self.shipstab, text='Ships')
        self.exporttab = ExportTab(self)
        self.add(self.exporttab, text='Export')
        self.messagetab = AISMessageTab(self)
        self.add(self.messagetab, text='Message Log')
        self.stninfotab = StationInfoTab(self)
        self.add(self.stninfotab, text='Station Information')


class MessageWindow(tkinter.Toplevel):
    """
    window to display details of individual AIS messages

    Args:
        window(tkinter.Tk): the main window this spawns from
    """

    def __init__(self, window):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.transient(self.window)
        self.msgdetailsbox = TextBoxTab(self)
        self.msgdetailsbox.pack()


class NetworkSettingsWindow(tkinter.Toplevel):
    """
    window to configure network settings

    Args:
        window(tkinter.Tk): the main window this spawns from
    """

    def __init__(self, window):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.title = 'Network Settings'
        serverhostlabel = tkinter.Label(self, text='Server IP')
        serverhostlabel.grid(column=0, row=0)
        self.serverhost = tkinter.Entry(self)
        self.serverhost.insert(0, self.window.netsettings['Server IP'])
        self.serverhost.grid(column=1, row=0)
        serverportlabel = tkinter.Label(self, text='Server Port')
        serverportlabel.grid(column=0, row=1)
        self.serverport = tkinter.Entry(self)
        self.serverport.insert(0, self.window.netsettings['Server Port'])
        self.serverport.grid(column=1, row=1)
        self.chk = tkinter.Checkbutton(
            self, text='forward NMEA Sentences to a remote host',
            var=self.window.forwardsentences)
        self.chk.grid(column=0, row=2)
        remotehostlabel = tkinter.Label(self, text='Remote Server IP')
        remotehostlabel.grid(column=0, row=3)
        self.remotehost = tkinter.Entry(self)
        self.remotehost.insert(0, self.window.netsettings['Remote Server IP'])
        self.remotehost.grid(column=1, row=3)
        remoteportlabel = tkinter.Label(self, text='Remote Server Port')
        remoteportlabel.grid(column=0, row=4)
        self.remoteport = tkinter.Entry(self)
        self.remoteport.insert(
            0, self.window.netsettings['Remote Server Port'])
        self.remoteport.grid(column=1, row=4)
        loglabel = tkinter.Label(self, text='Log NMEA Sentences')
        loglabel.grid(column=0, row=6)
        self.logpath = tkinter.Entry(self)
        self.logpath.insert(0, self.window.netsettings['Log File Path'])
        self.logpath.grid(column=0, row=7)
        logpathbutton = tkinter.Button(
            self, text='Choose Log Path', command=self.set_log_path)
        logpathbutton.grid(column=1, row=7)
        loglabel = tkinter.Label(self, text='Ouput Live KMZ Map')
        loglabel.grid(column=0, row=8)
        self.kmzpath = tkinter.Entry(self)
        self.kmzpath.insert(0, self.window.netsettings['KMZ File Path'])
        self.kmzpath.grid(column=0, row=9)
        kmzpathbutton = tkinter.Button(
            self, text='Choose KMZ Path', command=self.set_kmz_path)
        kmzpathbutton.grid(column=1, row=9)
        savesettingsbutton = tkinter.Button(
            self, text='Save Settings', command=self.save_settings)
        savesettingsbutton.grid(column=0, row=10)
        self.transient(self.window)

    def set_log_path(self):
        """
        open a dialogue box to choose where we save NMEA sentences to
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("nmea text file", "*.txt"),
                       ("All Files", "*.*")))
        self.logpath.insert(0, outputfile)

    def set_kmz_path(self):
        """
        open a dialogue box to choose where we save KMZ data to
        """
        outputdir = tkinter.filedialog.askdirectory()
        self.kmzpath.insert(0, outputdir)

    def save_settings(self):
        """
        get the settings from the form
        """
        if self.window.serverrunning:
            tkinter.messagebox.showwarning(
                'Network Settings',
                'cannot change settings whilst server is running')
        else:
            self.window.netsettings['Server IP'] = self.serverhost.get()
            self.window.netsettings['Server Port'] = int(self.serverport.get())
            self.window.netsettings['Remote Server IP'] = self.remotehost.get()
            self.window.netsettings['Remote Server Port'] = int(
                self.remoteport.get())
            self.window.netsettings['Log File Path'] = self.logpath.get()
            self.window.netsettings['KMZ File Path'] = self.kmzpath.get()
            tkinter.messagebox.showinfo(
                'Network Settings', 'Network Settings Saved')
        self.destroy()


class BasicGUI(tkinter.Tk):
    """
    a basic GUI using tkinter to control the program

    Attributes:
        nmeatracker(nmea.NMEAtracker): deals with the NMEA sentences
        aistracker(ais.AISTracker): decodes the AIS messages
        messagedict(dict): stores all the messages
        statuslabel(tkinter.Label): forms the status bar at the top of the
                                    main window
        mpq(multiprocessing.Queue): used to communicate with the
                                      server process
        updateguithread(threading.Thread): updates the GUI, is None on init
        refreshguithread(threading.Thread):refreshes the GUI, is None on init
        serverprocess(multiprocessing.Process): process that listens for AIS
            sentences on the network, is None on init
        serverrunning(bool): true if the server is running
        stopevent(threading.Event): stop even to stop the threads
        forwardsentences(tkinter.BooleanVar): should sentences be
                                              forwarded to another server
        livemap(bool): should a live KML map be created
    """

    netsettings = {
        'Server IP': '127.0.0.1',
        'Server Port': 10110,
        'Remote Server IP': '127.0.0.1',
        'Remote Server Port': 10111,
        'Log File Path': '',
        'KMZ File Path': ''}

    def __init__(self):
        tkinter.Tk.__init__(self)
        self.nmeatracker = nmea.NMEAtracker()
        self.aistracker = ais.AISTracker()
        self.messagedict = {}
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.title('AIS NMEA 0183 Decoder')
        self.statuslabel = tkinter.Label(self, text='', bg='light grey')
        self.statuslabel.pack(fill=tkinter.X)
        self.tabcontrol = TabControl(self)
        self.tabcontrol.pack(expand=1, fill='both')
        self.top_menu()
        self.mpq = multiprocessing.Queue()
        self.updateguithread = None
        self.refreshguithread = None
        self.serverprocess = None
        self.serverrunning = False
        self.stopevent = threading.Event()
        self.forwardsentences = tkinter.BooleanVar()
        self.forwardsentences.set(0)
        self.livemap = None

    def clear_gui(self):
        """
        clear the gui of all data
        """
        res = tkinter.messagebox.askyesno('Clearing GUI', 'Are you sure?')
        if res:
            if self.serverrunning:
                tkinter.messagebox.showwarning(
                    'WARNING', 'Cannot clear GUI whilst server is running')
            else:
                self.statuslabel.config(text='', bg='light grey')
                self.tabcontrol.statstab.aismsgtotal.configure(text='')
                self.tabcontrol.statstab.nmeasentencetotal.configure(text='')
                self.tabcontrol.statstab.nmeamultipartassembled.configure(
                    text='')
                self.tabcontrol.statstab.totalstns.configure(text='')
                self.tabcontrol.statstab.starttime.configure(text='')
                self.tabcontrol.statstab.latesttime.configure(text='')
                self.tabcontrol.statstab.msgstatstxt.delete(1.0, tkinter.END)
                self.tabcontrol.statstab.shiptypestxt.delete(1.0, tkinter.END)
                self.tabcontrol.statstab.flagstxt.delete(1.0, tkinter.END)
                self.tabcontrol.shipstab.tree.delete(
                    *self.tabcontrol.shipstab.tree.get_children())
                self.tabcontrol.messagetab.tree.delete(
                    *self.tabcontrol.messagetab.tree.get_children())
                self.tabcontrol.stninfotab.stnoptions['values'] = []
                self.aistracker.stations.clear()
                self.aistracker.messages.clear()
                self.aistracker.timings.clear()
                self.aistracker.messagesprocessed = 0
                self.nmeatracker.multiparts.clear()
                self.nmeatracker.channelcounter.clear()
                self.nmeatracker.sentencecount = 0
                self.nmeatracker.reassembled = 0
                self.messagedict.clear()

    def top_menu(self):
        """
        format and add the top menu to the main window
        """
        menu = tkinter.Menu(self)
        openfileitem = tkinter.Menu(menu, tearoff=0)
        openfileitem.add_command(label='Open', command=self.open_file)
        openfileitem.add_command(label='Clear GUI', command=self.clear_gui)
        openfileitem.add_command(label='Quit', command=self.quit)
        menu.add_cascade(label='File', menu=openfileitem)
        networkitem = tkinter.Menu(menu, tearoff=0)
        networkitem.add_command(
            label='Settings', command=self.network_settings)
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

    def network_settings(self):
        """
        open the network settings window
        """
        NetworkSettingsWindow(self)

    def about(self):
        """
        display version, licence and who created it
        """
        messagewindow = MessageWindow(self)
        messagewindow.msgdetailsbox.append_text(guihelp.LICENCE)

    def help(self):
        """
        display the help window
        """
        guihelp.HelpWindow(self)

    def start_server(self):
        """
        start the server
        """
        self.serverrunning = True
        self.tabcontrol.statstab.starttime.configure(
            text=datetime.datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S'))
        if self.netsettings['KMZ File Path'] != '':
            self.livemap = livekmlmap.AdvancedLiveKMLMap(
                self.netsettings['KMZ File Path'])
            self.livemap.create_netlink_file()
        if self.forwardsentences.get() == 1:
            print('forwarding sentences')
            self.serverprocess = multiprocessing.Process(
                target=network.mpserver,
                args=[self.mpq, self.netsettings['Server IP'],
                      self.netsettings['Server Port'],
                      self.netsettings['Remote Server IP'],
                      self.netsettings['Remote Server Port']],
                kwargs={'logpath': self.netsettings['Log File Path']})
        else:
            self.serverprocess = multiprocessing.Process(
                target=network.mpserver,
                args=[self.mpq, self.netsettings['Server IP'],
                      self.netsettings['Server Port']],
                kwargs={'logpath': self.netsettings['Log File Path']})
        self.serverprocess.start()
        tkinter.messagebox.showinfo('Network', 'Server Started')
        self.updateguithread = threading.Thread(
            target=self.updategui, args=(self.stopevent,))
        self.updateguithread.setDaemon(True)
        self.updateguithread.start()
        self.refreshguithread = threading.Thread(
            target=self.refreshgui, args=(self.stopevent,))
        self.refreshguithread.setDaemon(True)
        self.refreshguithread.start()
        self.statuslabel.config(
            text='AIS Server Listening on {} port {}'.format(
                self.netsettings['Server IP'],
                self.netsettings['Server Port']),
            fg='black', bg='green2')

    def stop_server(self):
        """
        stop the server
        """
        self.serverrunning = False
        self.serverprocess.terminate()
        self.stopevent.set()
        self.updateguithread.join(timeout=1)
        self.refreshguithread.join(timeout=1)
        self.serverprocess = None
        self.updateguithread = None
        self.refreshguithread = None
        tkinter.messagebox.showinfo('Network', 'Server Stopped')
        self.statuslabel.config(text='', bg='light grey')
        self.stopevent.clear()

    def open_file(self):
        """
        pop open a file browser to allow the user to choose which NMEA 0183
        text file they want to process and then process it
        """
        if self.serverrunning:
            tkinter.messagebox.showwarning(
                'WARNING', 'Stop Server First')
        else:
            inputfile = tkinter.filedialog.askopenfilename(
                filetypes=(
                    ("comma seperated values", "*.csv"),
                    ("javascript object notation lines", "*.jsonl"),
                    ("All Files", "*.*")))
            self.statuslabel.config(
                text='Loading capture file - {}'.format(inputfile),
                fg='black', bg='gold')
            self.update_idletasks()
            try:
                if inputfile.endswith('.csv'):
                    self.aistracker, self.messagedict = capturefile.aistracker_from_csv(inputfile)
                    self.nmeatracker.sentencecount = 'N/A'
                    self.nmeatracker.reassembled = 'N/A'
                elif inputfile.endswith('.jsonl'):
                    self.aistracker, self.messagedict = capturefile.aistracker_from_json(inputfile)
                    self.nmeatracker.sentencecount = 'N/A'
                    self.nmeatracker.reassembled = 'N/A'
                else:
                    self.aistracker, self.nmeatracker, self.messagedict = \
                        capturefile.aistracker_from_file(inputfile, debug=True)
            except (FileNotFoundError, TypeError):
                self.statuslabel.config(text='', bg='light grey')
                return
            self.tabcontrol.stninfotab.stn_options()
            try:
                self.tabcontrol.statstab.starttime.configure(
                    text=self.aistracker.timings[0])
            except IndexError:
                self.tabcontrol.statstab.starttime.configure(
                    text='Unavailable')
            self.tabcontrol.statstab.write_stats()
            self.tabcontrol.statstab.write_stats_verbose()
            self.tabcontrol.shipstab.create_ship_table()
            self.tabcontrol.messagetab.create_message_table()
            for payload in self.messagedict:
                latestmsg = [payload, self.messagedict[payload].description,
                             self.messagedict[payload].mmsi,
                             self.messagedict[payload].rxtime]
                self.tabcontrol.messagetab.add_new_line(latestmsg)
            self.statuslabel.config(
                text='Loaded capture file - {}'.format(inputfile),
                fg='black', bg='light grey')

    def updategui(self, stopevent):
        """
        update the nmea and ais trackers from the network

        run in another thread whist the server is running and
        recieving packets, get NMEA sentences from the queue and process them

        Args:
            stopevent(threading.Event): a threading stop event
        """
        while not stopevent.is_set():
            qdata = self.mpq.get()
            if qdata:
                try:
                    payload = self.nmeatracker.process_sentence(qdata)
                    if payload:
                        currenttime = datetime.datetime.utcnow().strftime(
                            '%Y/%m/%d %H:%M:%S')
                        try:
                            msg = self.aistracker.process_message(
                                payload, timestamp=currenttime)
                        except (IndexError, KeyError) as err:
                            errmsg = '{} - error with - {}'.format(
                                str(err), payload)
                            AISLOGGER.error(errmsg)
                        self.messagedict[payload] = msg
                        latestmsg = [payload, msg.description,
                                     msg.mmsi, currenttime]
                        self.tabcontrol.messagetab.add_new_line(latestmsg)
                        self.tabcontrol.statstab.write_stats()
                except (nmea.NMEAInvalidSentence, nmea.NMEACheckSumFailed,
                        ais.UnknownMessageType, ais.InvalidMMSI) as err:
                    AISLOGGER.debug(str(err))
                    continue
                except IndexError:
                    AISLOGGER.debug('no data on line')
                    continue

    def refreshgui(self, stopevent):
        """
        refresh and update the gui every 10 seconds, run in another thread

        Args:
            stopevent(threading.Event): a threading stop event
        """
        while not stopevent.is_set():
            currenttime = datetime.datetime.utcnow().strftime(
                '%Y/%m/%d %H:%M:%S')
            if currenttime.endswith('5'):
                self.tabcontrol.shipstab.create_ship_table()
                self.tabcontrol.statstab.write_stats_verbose()
                self.tabcontrol.stninfotab.stn_options()
                self.tabcontrol.stninfotab.show_stn_info()
                if self.livemap:
                    self.livemap.create_detailed_map(
                        aistracker=self.aistracker)
                time.sleep(1)

    def quit(self):
        """
        open a confirmation box asking if the user wants to quit if yes then
        stop the server and exit the program
        """
        res = tkinter.messagebox.askyesno('Exiting Program', 'Are you sure?')
        if res:
            if self.serverrunning:
                self.stop_server()
            self.destroy()


if __name__ == '__main__':
    AISGUI = BasicGUI()
    AISGUI.mainloop()
