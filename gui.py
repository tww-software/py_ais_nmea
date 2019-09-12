import csv
import sys
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.ttk


import ais
import capturefile
import nmea



class MyGUI():

    def __init__(self):
        self.nmeatracker = nmea.NMEAtracker()
        self.aistracker = ais.AISTracker()
        self.window = tkinter.Tk()
        self.window.title('AIS NMEA 0183 Decoder')
        tabcontrol = tkinter.ttk.Notebook(self.window)
        tab1 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(tab1, text='Stats')
        self.tab2 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab2, text='Ships')
        self.tab3 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(self.tab3, text='Export')
        self.exportoptions = tkinter.ttk.Combobox(self.tab3)
        tabcontrol.pack(expand=1, fill='both')
        self.txt = tkinter.scrolledtext.ScrolledText(tab1)
        self.txt.pack(side='left', fill='both', expand=tkinter.TRUE)
        menu = tkinter.Menu(self.window)
        openfileitem = tkinter.Menu(menu, tearoff=0)
        openfileitem.add_command(label='Open', command=self.open_file)
        openfileitem.add_command(label='Quit', command=self.quit)
        menu.add_cascade(label='File', menu=openfileitem)
        self.window.config(menu=menu)


    def quit(self):
        res = tkinter.messagebox.askyesno('Exiting Program','Are you sure?')
        if res:
            sys.exit(0)

    def export_csv(self):
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("comma seperated values", "*.csv"),
                       ("All Files", "*.*") ))
        tabledata = self.aistracker.create_table_data()
        ais.write_csv_file(tabledata, outputfile)

    def export_tsv(self):
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".tsv",
            filetypes=(("tab seperated values", "*.tsv"),
                       ("All Files", "*.*") ))
        tabledata = self.aistracker.create_table_data()
        ais.write_csv_file(tabledata, outputfile, dialect='excel-tab')

    def export_kml(self):
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=(("keyhole markup language", "*.kml"),
                       ("All Files", "*.*") ))
        self.aistracker.create_kml_map(outputfile, kmzoutput=False)

    def export_kmz(self):
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".kmz",
            filetypes=(("keyhole markup language KMZ", "*.kmz"),
                       ("All Files", "*.*") ))
        self.aistracker.create_kml_map(outputfile, kmzoutput=True)

    def export_json(self):
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("javascript object notation", "*.json"),
                       ("All Files", "*.*") ))
        joutdict = {}
        joutdict['NMEA Stats'] = self.nmeatracker.nmea_stats()
        joutdict['AIS Stats'] = self.aistracker.tracker_stats()
        joutdict['AIS Stations'] = self.aistracker.all_station_info()
        ais.write_json_file(joutdict, outputfile)

    def export_geojson(self):
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".geojson",
            filetypes=(("geo json", "*.geojson"),
                       ("All Files", "*.*") ))
        self.aistracker.create_geojson_map(outputfile)

    def open_file(self):
        inputfile = tkinter.filedialog.askopenfilename()
        self.aistracker, self.nmeatracker, _ = capturefile.aistracker_from_file(inputfile)
        self.export_buttons()
        self.write_stats()
        self.create_ship_table()

    def write_stats(self):
        self.txt.delete(1.0, tkinter.END)
        self.txt.insert(tkinter.INSERT, self.aistracker.__str__())
        self.txt.insert(tkinter.INSERT, '\n\n')
        self.txt.insert(tkinter.INSERT, self.nmeatracker.__str__())
        printablestats = ais.create_summary_text(self.aistracker.tracker_stats())
        self.txt.insert(tkinter.INSERT, '\n\n')
        self.txt.insert(tkinter.INSERT, printablestats)

    def create_ship_table(self):
        tree = tkinter.ttk.Treeview(self.tab2)
        verticalscrollbar = tkinter.ttk.Scrollbar(self.tab2, orient=tkinter.VERTICAL, command=tree.yview)
        verticalscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        horizontalscrollbar = tkinter.ttk.Scrollbar(self.tab2, orient=tkinter.HORIZONTAL, command=tree.xview)
        horizontalscrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        tabledata = self.aistracker.create_table_data()
        headers = tabledata.pop(0)
        tree["columns"] = headers
        for column in headers:
            tree.column(column, width=200, minwidth=70, stretch=tkinter.NO)
            tree.heading(column, text=column, anchor=tkinter.W)
        counter = 0
        for line in tabledata:
            tree.insert('', counter, values=line)
            counter += 1
        tree.pack(side=tkinter.TOP, fill='both', expand=tkinter.TRUE)

    def export_buttons(self):
        self.exportoptions['values']= ('CSV', 'TSV', 'KML', 'KMZ', 'JSON', 'GEOJSON')
        self.exportoptions.set('KMZ')
        self.exportoptions.grid(column=1, row=1)
        self.exportbutton = tkinter.Button(self.tab3, text='Export', command=self.export_files)
        self.exportbutton.grid(column=2, row=1)

    def export_files(self):
        commands = {'CSV': self.export_csv,
                    'TSV': self.export_tsv,
                    'KML': self.export_kml,
                    'KMZ': self.export_kmz,
                    'JSON': self.export_json,
                    'GEOJSON': self.export_geojson}
        option = self.exportoptions.get()
        commands[option]()

    def display_gui(self):
        self.window.mainloop()

if __name__ == '__main__':
    mygui = MyGUI()
    mygui.display_gui()
