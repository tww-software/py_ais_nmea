"""
tab to display a table of all the ships and AIS stations we can see
"""

import tkinter
import pyaisnmea.ais as ais

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

    def on_tree_item_doubleclick(self, event=None):
        """
        if the user double clicks on a row in the tree
        grab the MMSI of that row and switch to the station information tab
        (stninfotab) and display more detailed info
        """
        item = self.tree.identify('item', event.x, event.y)
        clickedmmsi = str(self.tree.item(item)['values'][0])
        if len(clickedmmsi) == 7:
            clickedmmsi = '00' + clickedmmsi
        stnobj = self.tabs.window.aistracker.stations[clickedmmsi]
        lookup = '{}  {}'.format(clickedmmsi, stnobj.name)
        self.tabs.stninfotab.stnoptions.set(lookup)
        self.tabs.stninfotab.show_stn_info()
        self.tabs.select(self.tabs.stninfotab)

    def create_ship_table(self, new=True):
        """
        draw a large table in shipstab of all the AIS stations we have
        """
        if new:
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = ais.NAVHEADERS
            for column in ais.NAVHEADERS:
                self.tree.column(column, width=200, minwidth=70,
                                 stretch=tkinter.YES)
                self.tree.heading(column, text=column, anchor=tkinter.W)
                        
        tabledata = self.tabs.window.aistracker.create_nav_table()      
        for line in tabledata:
            try:
                self.tree.insert('', 'end', values=line, iid=str(line[0]))
            except tkinter.TclError as err:
                self.tree.item(item=str(line[0]), values=line)            
        if new:
            self.tree.pack(side=tkinter.TOP, fill='both', expand=tkinter.TRUE)
            self.tree['show'] = 'headings'
