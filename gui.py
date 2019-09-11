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
        tab2 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(tab2, text='Ships')
        tab3 = tkinter.ttk.Frame(tabcontrol)
        tabcontrol.add(tab3, text='Export')
        tabcontrol.pack(expand=1, fill='both')
        self.txt = tkinter.scrolledtext.ScrolledText(tab1)
        self.txt.grid(column=0,row=1)
        exportcsvbutton = tkinter.Button(tab3, text='Export CSV', command=self.export_csv)
        exportcsvbutton.grid(column=1, row=1)
        exportcsvbutton = tkinter.Button(tab3, text='Export TSV', command=self.export_tsv)
        exportcsvbutton.grid(column=1, row=3)
        exportkmlbutton = tkinter.Button(tab3, text='Export KML', command=self.export_kml)
        exportkmlbutton.grid(column=1, row=5)
        exportkmzbutton = tkinter.Button(tab3, text='Export KMZ', command=self.export_kmz)
        exportkmzbutton.grid(column=1, row=7)
        exportkmzbutton = tkinter.Button(tab3, text='Export JSON', command=self.export_json)
        exportkmzbutton.grid(column=1, row=9)
        exportkmzbutton = tkinter.Button(tab3, text='Export GEOJSON', command=self.export_geojson)
        exportkmzbutton.grid(column=1, row=11)
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
        self.txt.delete(1.0, tkinter.END)
        self.txt.insert(tkinter.INSERT, '...Loading...')
        inputfile = tkinter.filedialog.askopenfilename()
        self.aistracker, self.nmeatracker, _ = capturefile.aistracker_from_file(inputfile)
        self.txt.delete(1.0, tkinter.END)
        self.txt.insert(tkinter.INSERT, self.aistracker.__str__())
        self.txt.insert(tkinter.INSERT, '\n\n')
        self.txt.insert(tkinter.INSERT, self.nmeatracker.__str__())
        printablestats = ais.create_summary_text(self.aistracker.tracker_stats())
        self.txt.insert(tkinter.INSERT, '\n\n')
        self.txt.insert(tkinter.INSERT, printablestats)

    def display_gui(self):
        self.window.mainloop()

if __name__ == '__main__':
    mygui = MyGUI()
    mygui.display_gui()
