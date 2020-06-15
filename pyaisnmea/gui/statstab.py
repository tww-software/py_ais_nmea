"""
tab that displays overall stats about the stations received
"""

import tkinter

import pyaisnmea.ais as ais


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
