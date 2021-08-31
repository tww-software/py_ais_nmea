"""
tab that displays overall stats about the stations received
"""

import tkinter

import pyaisnmea.export as export


class StatsTab(tkinter.ttk.Frame):
    """
    provide overall statistics for all the AIS Stations we can see

    Args:
        tabcontrol(tkinter.ttk.Notebook): ttk notebook to add this tab to
    """

    def __init__(self, tabcontrol):
        tkinter.ttk.Frame.__init__(self, tabcontrol)
        self.tabs = tabcontrol
        statscounters = tkinter.Frame(self)
        aismsgtotallabel = tkinter.Label(
            statscounters, text='Total AIS messages')
        aismsgtotallabel.grid(column=0, row=0)
        self.aismsgtotal = tkinter.Label(statscounters, text='')
        self.aismsgtotal.grid(column=1, row=0)
        nmeasentencetotallabel = tkinter.Label(
            statscounters, text='Total NMEA sentences')
        nmeasentencetotallabel.grid(column=0, row=1)
        self.nmeasentencetotal = tkinter.Label(statscounters, text='')
        self.nmeasentencetotal.grid(column=1, row=1)
        nmeamultipartassembledlabel = tkinter.Label(
            statscounters, text='NMEA multipart sentences reassembled')
        nmeamultipartassembledlabel.grid(column=0, row=2)
        self.nmeamultipartassembled = tkinter.Label(statscounters, text='')
        self.nmeamultipartassembled.grid(column=1, row=2)
        totalstnslabel = tkinter.Label(
            statscounters, text='Total Unique Stations')
        totalstnslabel.grid(column=0, row=3)
        self.totalstns = tkinter.Label(statscounters, text='')
        self.totalstns.grid(column=1, row=3)
        starttimelabel = tkinter.Label(statscounters, text='Start Time')
        starttimelabel.grid(column=0, row=4)
        self.starttime = tkinter.Label(statscounters, text='')
        self.starttime.grid(column=1, row=4)
        latesttimelabel = tkinter.Label(statscounters, text='Latest Time')
        latesttimelabel.grid(column=0, row=5)
        self.latesttime = tkinter.Label(statscounters, text='')
        self.latesttime.grid(column=1, row=5)
        statscounters.pack(side='top')
        statsboxes = tkinter.PanedWindow(self)
        self.msgstatstxt = tkinter.scrolledtext.ScrolledText(statsboxes)
        self.msgstatstxt.configure()
        statsboxes.add(self.msgstatstxt)
        self.shiptypestxt = tkinter.scrolledtext.ScrolledText(statsboxes)
        self.shiptypestxt.configure()
        statsboxes.add(self.shiptypestxt)
        self.flagstxt = tkinter.scrolledtext.ScrolledText(statsboxes)
        self.flagstxt.configure()
        statsboxes.add(self.flagstxt)
        statsboxes.pack(fill=tkinter.BOTH, expand=1)
        for pane in statsboxes.panes():
            statsboxes.paneconfigure(pane, minsize=250) 

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
            export.create_summary_text(stats['Message Stats']))
        self.shiptypestxt.insert(
            tkinter.INSERT,
            export.create_summary_text(stats['Ship Types']))
        self.flagstxt.insert(
            tkinter.INSERT,
            export.create_summary_text(stats['Country Flags']))
