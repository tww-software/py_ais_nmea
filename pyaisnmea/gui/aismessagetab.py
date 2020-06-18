"""
tab to display a table of all the AIS messages we have recieved
"""

import tkinter

import pyaisnmea.ais as ais


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

    def __init__(self, window):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.transient(self.window)
        self.msgdetailsbox = TextBoxTab(self)
        self.msgdetailsbox.pack()


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
