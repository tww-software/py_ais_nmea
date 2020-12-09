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


class ExportAborted(Exception):
    """
    raise if we cancel an export operation
    """
    pass


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
        self.orderby = tkinter.ttk.Combobox(self, state='readonly')
        self.exporthelplabel = tkinter.Label(self)
        self.region = tkinter.StringVar()
        self.regionlabel = tkinter.Label(self)
        self.export_options()
        self.exportoptions.bind("<<ComboboxSelected>>", self.show_export_help)
        self.show_export_help()

    def region_selected_help(self):
        currentregion = self.region.get()
        atext = 'Europe, Africa, Asia, Oceania, Greenland.'
        btext = ('North & South America, Japan, South Korea, '
                 'the Philippines, Taiwan, Hawaii, Easter Island.')
        if currentregion == 'A':
            self.regionlabel.config(text=atext)
        elif currentregion == 'B':
            self.regionlabel.config(text=btext)

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
        self.exporthelplabel.grid(column=2, row=1)
        self.orderby['values'] = ('Flags', 'Class', 'Types')
        self.orderby.set('Types')
        self.orderby.grid(column=1, row=2)
        orderbylabel = tkinter.Label(self)
        orderbylabel.configure(
            text='Output Order (for KMZ,KML and EVERYTHING)')
        orderbylabel.grid(column=2, row=2)
        radioa = tkinter.Radiobutton(
            self, text="IALA Region A", variable=self.region, value='A',
            command=self.region_selected_help)
        radiob = tkinter.Radiobutton(
            self, text="IALA Region B", variable=self.region, value='B',
            command=self.region_selected_help)
        radioa.grid(column=1, row=3)
        radiob.grid(column=2, row=3)
        radioa.select()
        self.region_selected_help()
        self.regionlabel.grid(column=4, row=3)
        exportbutton = tkinter.Button(self, text='Export',
                                      command=self.export_files)
        exportbutton.grid(column=1, row=4)

    def export_files(self):
        """
        choose which export command to run from the exportoptions drop down
        in the Export tab
        """
        if self.tabs.window.serverrunning:
            tkinter.messagebox.showwarning(
                'WARNING', 'Cannot export files whilst server is running')
        elif self.tabs.window.aistracker.messagesprocessed == 0:
            tkinter.messagebox.showwarning(
                'WARNING', 'Nothing to export.')
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

        Raises:
            ExportAborted: if the user clicks cancel
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("comma seperated values", "*.csv"),
                       ("All Files", "*.*")))
        if outputfile:
            tabledata = self.tabs.window.aistracker.create_table_data()
            export.write_csv_file(tabledata, outputfile)
        else:
            raise ExportAborted('Export cancelled by user.')

    def export_tsv(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location

        Raises:
            ExportAborted: if the user clicks cancel
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".tsv",
            filetypes=(("tab seperated values", "*.tsv"),
                       ("All Files", "*.*")))
        if outputfile:
            tabledata = self.tabs.window.aistracker.create_table_data()
            export.write_csv_file(tabledata, outputfile, dialect='excel-tab')
        else:
            raise ExportAborted('Export cancelled by user.')

    def export_kml(self, kmz=False):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location

        Raises:
            ExportAborted: if the user clicks cancel
        """
        orderby = self.orderby.get()
        currentregion = self.region.get()
        if kmz:
            outputfile = tkinter.filedialog.asksaveasfilename(
                defaultextension=".kmz",
                filetypes=(("keyhole markup language", "*.kmz"),
                           ("All Files", "*.*")))
        else:
            outputfile = tkinter.filedialog.asksaveasfilename(
                defaultextension=".kml",
                filetypes=(("keyhole markup language", "*.kml"),
                           ("All Files", "*.*")))
        if outputfile:
            self.tabs.window.aistracker.create_kml_map(
                outputfile, kmzoutput=kmz, orderby=orderby,
                region=currentregion)
        else:
            raise ExportAborted('Export cancelled by user.')

    def export_kmz(self):
        """
        calls export_kml with kmz as True
        """
        self.export_kml(kmz=True)

    def export_json(self, verbosejson=False):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location

        Raises:
            ExportAborted: if the user clicks cancel
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("javascript object notation", "*.json"),
                       ("All Files", "*.*")))
        if outputfile:
            joutdict = {}
            joutdict['NMEA Stats'] = self.tabs.window.nmeatracker.nmea_stats()
            joutdict['AIS Stats'] = self.tabs.window.aistracker.tracker_stats()
            joutdict['AIS Stations'] = self.tabs.window.aistracker. \
                all_station_info(verbose=verbosejson)
            export.write_json_file(joutdict, outputfile)
        else:
            raise ExportAborted('Export cancelled by user.')

    def export_verbose_json(self):
        """
        json file with all postion reports for each vessel
        """
        self.export_json(verbosejson=True)

    def export_geojson(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location

        Raises:
            ExportAborted: if the user clicks cancel
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".geojson",
            filetypes=(("geo json", "*.geojson"),
                       ("All Files", "*.*")))
        if outputfile:
            self.tabs.window.aistracker.create_geojson_map(outputfile)
        else:
            raise ExportAborted('Export cancelled by user.')

    def export_debug(self):
        """
        pop open a file browser to allow the user to choose where to save the
        file and then save file to that location

        Raises:
            ExportAborted: if the user clicks cancel
        """
        outpath = tkinter.filedialog.askdirectory()
        if outpath:
            jsonlines, messagecsvlist = \
                self.tabs.window.messagelog.debug_output()
            export.write_json_lines(
                jsonlines, os.path.join(outpath, 'ais-messages.jsonl'))
            export.write_csv_file(
                messagecsvlist, os.path.join(outpath, 'ais-messages.csv'))
        else:
            raise ExportAborted('Export cancelled by user.')

    def export_overview(self, outpath=None):
        """
        export the most popular file formats
        KMZ - map
        JSON & CSV - vessel details
        JSONLINES and CSV - message debug

        Args:
            outpath(str): path to export to if called from another function

        Raises:
            ExportAborted: if the user clicks cancel
        """
        orderby = self.orderby.get()
        currentregion = self.region.get()
        if not outpath:
            outpath = tkinter.filedialog.askdirectory()
            if outpath:
                export.export_overview(
                    self.tabs.window.aistracker,
                    self.tabs.window.nmeatracker,
                    self.tabs.window.messagelog,
                    outpath, orderby=orderby, region=currentregion)
            else:
                raise ExportAborted('Export cancelled by user.')

    def export_everything(self):
        """
        export overview and files for each individual station

        Raises:
            ExportAborted: if the user clicks cancel
        """
        orderby = self.orderby.get()
        currentregion = self.region.get()
        previoustext = self.tabs.window.statuslabel['text']
        res = tkinter.messagebox.askyesno(
            'Export Everything',
            'Exporting data on all AIS stations, this may take some time.')
        if res:
            outpath = tkinter.filedialog.askdirectory()
            if outpath:
                self.tabs.window.statuslabel.config(
                    text='Exporting all AIS station data to - {}'.format(
                        outpath),
                    fg='black', bg='gold')
                self.update_idletasks()
                export.export_overview(
                    self.tabs.window.aistracker,
                    self.tabs.window.nmeatracker,
                    self.tabs.window.messagelog,
                    outpath, orderby=orderby, region=currentregion)
                export.export_everything(
                    self.tabs.window.aistracker,
                    self.tabs.window.messagelog,
                    outpath, orderby=orderby, region=currentregion)
                self.tabs.window.statuslabel.config(
                    text=previoustext, bg='light grey')
            else:
                raise ExportAborted(
                    'Export of all AIS data cancelled by user.')
        else:
            raise ExportAborted('Export of all AIS data cancelled by user.')
