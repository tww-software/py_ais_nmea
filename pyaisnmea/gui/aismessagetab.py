"""
tab to display a table of all the AIS messages we have received
"""

import tkinter

import pyaisnmea.export as export


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
        self.aisbox = tkinter.scrolledtext.ScrolledText(
            self, selectbackground='cyan')
        self.aisbox.pack(side='left', fill='both', expand=tkinter.TRUE)
        self.aisbox.bind('<Control-c>', self.copy)
        self.aisbox.bind('<Control-C>', self.copy)
        self.aisbox.bind('<Control-a>', self.select_all)
        self.aisbox.bind('<Control-A>', self.select_all)
        self.aisbox.bind('<Button-3>', self.select_all)

    def append_text(self, text):
        """
        write text into the box and append a newline after it

        Args:
            text(str): text to write in the box
        """
        self.aisbox.insert(tkinter.INSERT, text)
        self.aisbox.insert(tkinter.INSERT, '\n\n')
        self.aisbox.see(tkinter.END)

    def copy(self, event):
        """
        put highlighted text onto the clipboard when ctrl+c is used

        Args:
            event(tkinter.Event): event from the user (ctrl + c)
        """
        try:
            self.aisbox.clipboard_clear()
            self.aisbox.clipboard_append(
                self.aisbox.selection_get())
        except tkinter.TclError:
            pass

    def select_all(self, event):
        """
        select all the text in the textbox when ctrl+a is used

        Args:
            event(tkinter.Event): event from the user (ctrl + a)
        """
        self.aisbox.tag_add(tkinter.SEL, "1.0", tkinter.END)
        self.aisbox.mark_set(tkinter.INSERT, "1.0")
        self.aisbox.see(tkinter.INSERT)
        return 'break'


class MessageWindow(tkinter.Toplevel):
    """
    window to display details of individual AIS messages

    Args:
        window(tkinter.Tk): the main window this spawns from
    """

    def __init__(self, window, mmsi=None):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.mmsi = str(mmsi)
        self.transient(self.window)
        self.msgdetailsbox = TextBoxTab(self)
        self.msgdetailsbox.pack(side=tkinter.TOP)
        if mmsi:
            lookupbutton = tkinter.Button(
                self, text='Lookup Station', command=self.lookup_stn)
            lookupbutton.pack(side=tkinter.BOTTOM)

    def lookup_stn(self):
        """
        find the station that sent the message and display its info in the
        AIS Stations tab on the main GUI window
        """
        if len(self.mmsi) == 7:
            self.mmsi = '00' + self.mmsi
        elif len(self.mmsi) == 8:
            self.mmsi = '0' + self.mmsi
        stnobj = self.window.tabs.window.aistracker.stations[self.mmsi]
        lookup = '{}  {}'.format(self.mmsi, stnobj.name)
        self.window.tabs.stninfotab.stnoptions.set(lookup)
        self.window.tabs.stninfotab.show_stn_info()
        self.window.tabs.select(self.window.tabs.stninfotab)


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
        self.autoscroll = tkinter.BooleanVar()
        self.autoscroll.set(1)
        self.autoscrollchk = tkinter.Checkbutton(
            self, text='autoscroll as new messages are added',
            var=self.autoscroll)
        self.autoscrollchk.select()
        self.autoscrollchk.pack(side=tkinter.TOP)
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
        self.msg_line_colours()
        self.tree.bind("<Double-1>", self.on_tree_item_doubleclick)

    def on_tree_item_doubleclick(self, event):
        """
        open a message box with further details when a user double clicks a
        message
        """
        item = self.tree.identify('item', event.x, event.y)
        clickedmsgno = self.tree.item(item)['values'][0]
        clickednmea = self.tree.item(item)['values'][1]
        clickedmmsi = self.tree.item(item)['values'][3]
        messagewindow = MessageWindow(self, mmsi=clickedmmsi)
        msgsummary = export.create_summary_text(
            self.tabs.window.messagelog.messagedict[
                (clickedmsgno, clickednmea)].__dict__)
        messagewindow.msgdetailsbox.append_text(msgsummary)

    def create_message_table(self):
        """
        draw a large table in messagetab of all the NMEA sentences we have
        """
        self.tree.delete(*self.tree.get_children())
        headers = ['Message No', 'NMEA', 'AIS', 'MMSI', 'Timestamp']
        self.tree["columns"] = headers
        for column in headers:
            self.tree.column(column, width=200, minwidth=70,
                             stretch=tkinter.YES)
            self.tree.heading(column, text=column, anchor=tkinter.W)
        self.tree.pack(side=tkinter.TOP, fill='both', expand=tkinter.TRUE)
        self.tree['show'] = 'headings'

    def msg_line_colours(self):
        """
        format lines based on message types
        """
        self.tree.tag_configure(
            'Type 4 - Base Station Report', background='orange')
        self.tree.tag_configure(
            'Type 5 - Static and Voyage Related Data',
            background='cornflower blue')
        self.tree.tag_configure(
            'Type 6 - Binary Adressed Message', background='salmon1')
        self.tree.tag_configure(
            'Type 7 - Binary Acknowlegement', background='salmon3')
        self.tree.tag_configure(
            'Type 8 - Binary Broadcast Message', background='salmon2')
        self.tree.tag_configure(
            'Type 9 - Standard SAR Aircraft Report', background='yellow')
        self.tree.tag_configure(
            'Type 10 - UTC Date Inquiry', background='dark orange')
        self.tree.tag_configure(
            'Type 11 - UTC Date Response', background='orange')
        self.tree.tag_configure(
            'Type 12 - Addressed Safety Related Message', background='yellow2')
        self.tree.tag_configure(
            'Type 13 - Safety Related Acknowlegement', background='yellow2')
        self.tree.tag_configure(
            'Type 14 - Safety Related Broadcast Message', background='yellow2')
        self.tree.tag_configure(
            'Type 15 - Interrogation', background='light slate gray')
        self.tree.tag_configure(
            'Type 16 - Assignment Mode Command', background='gray')
        self.tree.tag_configure(
            'Type 17 - DGNSS Broadcast Binary Message',
            background='sandy brown')
        self.tree.tag_configure(
            'Type 18 - Standard Class B CS Position Report',
            background='medium sea green')
        self.tree.tag_configure(
            'Type 19 - Extended Class B CS Position Report',
            background='medium sea green')
        self.tree.tag_configure(
            'Type 20 - Datalink Management Message', background='red')
        self.tree.tag_configure(
            'Type 21 - Aid to Navigation Report', background='aquamarine')
        self.tree.tag_configure(
            'Type 22 - Channel Management', background='light gray')
        self.tree.tag_configure(
            'Type 23 - Group Assignment Command', background='light gray')
        self.tree.tag_configure(
            'Type 24 - Static Data Report', background='light sea green')
        self.tree.tag_configure(
            'Type 25 - Single Slot Binary Message', background='LightPink1')
        self.tree.tag_configure(
            'Type 26 - Multiple Slot Binary Message', background='LightPink2')
        self.tree.tag_configure(
            'Type 27 - Long Range AIS Broadcast Message',
            background='medium purple')

    def add_new_line(self, line):
        """
        add a new line to the tree table and scroll down to it

        Note:
            line[2] is the message type refered to in msg_line_colours
        """
        self.tree.insert('', self.counter, values=line, tags=(line[2],))
        self.counter += 1
        if self.autoscroll.get() == 1:
            self.tree.yview_moveto(1)
