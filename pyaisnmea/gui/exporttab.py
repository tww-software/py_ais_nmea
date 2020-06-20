"""
tab to allow the user to export data in different formats
"""

import logging
import os
import tkinter

import pyaisnmea.ais as ais
import pyaisnmea.capturefile as capturefile


AISLOGGER = logging.getLogger(__name__)


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