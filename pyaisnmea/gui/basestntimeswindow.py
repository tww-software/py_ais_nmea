"""
a window that allows the user to choose AIS Base Stations
as timing references for NMEA0183 text files
"""

import tkinter


class BaseStationTimesWindow(tkinter.Toplevel):
    """
    window to configure timing sources for NMEA0183 text files

    Note:
        this is a modal window, that takes over from the main window and only
        releases execution to the main window once it is closed
        transient - keeps this window on top of the main one
        grab_set - stops commands on the main window
        wait_window - commands on the main window paused until this ones closes

    Args:
        window(tkinter.Tk): the main window this spawns from
        basestntable(list):list of lists - a table of all the AIS base stations
    """

    def __init__(self, window, basestntable):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.basestntable = basestntable
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
        self.create_basestn_table()
        self.basestnlistbox = tkinter.Listbox(self)
        self.configure_basestn_listbox()
        savesettingsbutton = tkinter.Button(
            self, text='Save Settings', command=self.save_settings)
        savesettingsbutton.pack()
        self.transient(self.window)
        self.grab_set()
        self.window.wait_window(self)

    def save_settings(self):
        """
        get the settings from the form
        """
        listboxvalues = self.basestnlistbox.get(0, tkinter.END)
        self.window.timingsources = listboxvalues
        self.destroy()

    def on_tree_item_doubleclick(self, event=None):
        """
        if the user double clicks on a row in the tree
        grab the base station MMSI of that row
        then add the base stations MMSI to the listbox
        """
        item = self.tree.identify('item', event.x, event.y)
        clickedmmsi = str(self.tree.item(item)['values'][1])
        if len(clickedmmsi) == 7:
            clickedmmsi = '00' + clickedmmsi
        if clickedmmsi not in self.basestnlistbox.get(0, tkinter.END):
            self.basestnlistbox.insert(0, clickedmmsi)

    def on_listbox_item_doubleclick(self, event=None):
        """
        remove a base station MMSI from the listbox if a user double clicks it
        """
        currentselection = self.basestnlistbox.curselection()
        listboxitem = self.basestnlistbox.get(currentselection)
        mmsiindex = self.basestnlistbox.get(0, tkinter.END).index(listboxitem)
        self.basestnlistbox.delete(mmsiindex)

    def create_basestn_table(self, new=True):
        """
        draw a table of all the AIS Base stations we have
        """
        treelabel = tkinter.Label(self, text='AIS Base Stations Available')
        treelabel.pack()
        if new:
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = self.basestntable[0]
            for column in self.basestntable[0]:
                self.tree.column(column, width=200, minwidth=70,
                                 stretch=tkinter.YES)
                self.tree.heading(column, text=column, anchor=tkinter.W)
        for line in self.basestntable:
            try:
                self.tree.insert('', 'end', values=line, iid=str(line[0]))
            except tkinter.TclError:
                self.tree.item(item=str(line[0]), values=line)
        if new:
            self.tree.pack(side=tkinter.TOP, fill='both', expand=tkinter.TRUE)
            self.tree['show'] = 'headings'

    def configure_basestn_listbox(self):
        """
        create a listbox to store the MMSIs of base stations we will use as
        timing sources
        """
        listboxlabel = tkinter.Label(self, text='Timing Sources')
        listboxlabel.pack()
        self.basestnlistbox.pack(
            side=tkinter.TOP, fill='both', expand=tkinter.TRUE)
        self.basestnlistbox.bind(
            '<Double-1>', self.on_listbox_item_doubleclick)
