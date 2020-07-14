"""
tab to allow the user to export data in different formats
"""

import logging
import os
import tkinter

import pyaisnmea.export as export


AISLOGGER = logging.getLogger(__name__)

EXPORTHELP = {
    'OVERVIEW': 'export CSV, JSON, KMZ and DEBUG files to a directory',
    'EVERYTHING': 'export OVERVIEW and details for every AIS Station',
    'CSV': ('Comma Separated Values file containing similar data'
            ' to the Ships tab'),
    'TSV':  ('Tab Separated Values file containing similar data'
             ' to the Ships tab'),
    'KML':  'plain KML file with no custom icons (default icons will be used)',
    'KMZ':  'Keyhole Markup Language Map with custom icons',
    'JSON': 'JSON file containing stats and AIS station last known positions',
    'VERBOSE JSON': ('JSON file containing stats and '
                     'all AIS station position reports'),
    'GEOJSON': 'GEOJSON map of all AIS Station positions',
    'DEBUG': ('outputs 2 files (CSV and JSON lines) '
              'output of all AIS decoded messages')}


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
        self.exporthelplabel = tkinter.Label(self)
        self.exporthelplabel.grid(column=3, row=1)
        self.exportoptions.bind("<<ComboboxSelected>>", self.show_export_help)
        self.show_export_help()

    def export_options(self):
        """
        populate the export options drop down menu with file export options
        and add an export button next to it
        """
        self.exportoptions['values'] = (
            'OVERVIEW', 'EVERYTHING', 'CSV', 'TSV', 'KML', 'KMZ', 'JSON',
            'VERBOSE JSON', 'GEOJSON', 'DEBUG')
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
                        'EVERYTHING': self.export_everything,
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
                tkinter.messagebox.showerror(type(err).__name__, str(err))

    def show_export_help(self, event=None):
        """
        Display help text for each export option as the user selects each one

        Args:
            event(tkinter.Event): event from the user changing the export
                                  combobox dropdown menu options
        """
        option = self.exportoptions.get()
        helptext = EXPORTHELP[option]
        self.exporthelplabel.configure(text=helptext)

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
        export.write_csv_file(tabledata, outputfile)

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
        export.write_csv_file(tabledata, outputfile, dialect='excel-tab')

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
        export.write_json_file(joutdict, outputfile)

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

    def export_debug(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location
        """
        outpath = tkinter.filedialog.askdirectory()
        jsonlines, messagecsvlist = self.tabs.window.messagelog.debug_output()
        export.write_json_lines(
            jsonlines, os.path.join(outpath, 'ais-messages.jsonl'))
        export.write_csv_file(
            messagecsvlist, os.path.join(outpath, 'ais-messages.csv'))

    def export_overview(self, outpath=None):
        """
        export the most popular file formats
        KMZ - map
        JSON & CSV - vessel details
        JSONLINES and CSV - message debug

        Args:
            outpath(str): path to export to if called from another function
        """
        if not outpath:
            outpath = tkinter.filedialog.askdirectory()
        export.export_overview(
            self.tabs.window.aistracker,
            self.tabs.window.nmeatracker,
            self.tabs.window.messagelog,
            outpath)

    def export_everything(self):
        """
        export overview and files for each individual station
        """
        outpath = tkinter.filedialog.askdirectory()
        self.export_overview(outpath=outpath)
        export.export_everything(
            self.tabs.window.aistracker,
            self.tabs.window.messagelog,
            outpath)
