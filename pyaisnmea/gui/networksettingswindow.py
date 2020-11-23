"""
a window to allow the user to configure the network settings for the
server
"""

import tkinter


class NetworkSettingsWindow(tkinter.Toplevel):
    """
    window to configure network settings

    Args:
        window(tkinter.Tk): the main window this spawns from
    """

    def __init__(self, window):
        tkinter.Toplevel.__init__(self, window)
        self.window = window
        self.network_settings_group()
        self.nmea_settings_group()
        self.kml_settings_group()

    def network_settings_group(self):
        """
        group all the network settings within a tkinter LabelFrame
        """
        netgroup = tkinter.LabelFrame(
            self, text="Network settings", padx=10, pady=10)
        netgroup.pack(fill="both", expand="yes")
        serverhostlabel = tkinter.Label(netgroup, text='Server IP')
        serverhostlabel.pack()
        self.serverhost = tkinter.Entry(netgroup)
        self.serverhost.insert(0, self.window.netsettings['Server IP'])
        self.serverhost.pack()
        serverportlabel = tkinter.Label(netgroup, text='Server Port')
        serverportlabel.pack()
        self.serverport = tkinter.Entry(netgroup)
        self.serverport.insert(0, self.window.netsettings['Server Port'])
        self.serverport.pack()
        self.chk = tkinter.Checkbutton(
            netgroup, text='forward NMEA Sentences to a remote host',
            var=self.window.forwardsentences)
        self.chk.pack()
        remotehostlabel = tkinter.Label(netgroup, text='Remote Server IP')
        remotehostlabel.pack()
        self.remotehost = tkinter.Entry(netgroup)
        self.remotehost.insert(0, self.window.netsettings['Remote Server IP'])
        self.remotehost.pack()
        remoteportlabel = tkinter.Label(netgroup, text='Remote Server Port')
        remoteportlabel.pack()
        self.remoteport = tkinter.Entry(netgroup)
        self.remoteport.insert(
            0, self.window.netsettings['Remote Server Port'])
        self.remoteport.pack()

    def nmea_settings_group(self):
        """
        group all the nmea settings within a tkinter LabelFrame
        """
        nmeagroup = tkinter.LabelFrame(
            self, text="NMEA logging settings", padx=20, pady=20)
        nmeagroup.pack(fill="both", expand="yes")
        loglabel = tkinter.Label(nmeagroup, text='Log NMEA Sentences')
        loglabel.pack()
        self.logpath = tkinter.Entry(nmeagroup)
        self.logpath.insert(0, self.window.netsettings['Log File Path'])
        self.logpath.pack()
        logpathbutton = tkinter.Button(
            nmeagroup, text='Choose Log Path', command=self.set_log_path)
        logpathbutton.pack()

    def kml_settings_group(self):
        """
        group all the kml settings within a tkinter LabelFrame
        """
        kmlgroup = tkinter.LabelFrame(
            self, text="Live KML map settings", padx=20, pady=20)
        kmlgroup.pack(fill="both", expand="yes")
        kmllabel = tkinter.Label(kmlgroup, text='Ouput Live KML Map')
        kmllabel.pack()
        self.kmlpath = tkinter.Entry(kmlgroup)
        self.kmlpath.insert(0, self.window.netsettings['KML File Path'])
        self.kmlpath.pack()
        kmlpathbutton = tkinter.Button(
            kmlgroup, text='Choose KML Path', command=self.set_kml_path)
        kmlpathbutton.pack()
        self.kmzchk = tkinter.Checkbutton(
            kmlgroup, text='KMZ map (full colour icons)',
            var=self.window.kmzlivemap)
        self.kmzchk.pack()

        savesettingsbutton = tkinter.Button(
            self, text='Save Settings', command=self.save_settings)
        savesettingsbutton.pack()
        self.transient(self.window)

    def set_log_path(self):
        """
        open a dialogue box to choose where we save NMEA sentences to
        """
        outputfile = tkinter.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("nmea text file", "*.txt"),
                       ("All Files", "*.*")))
        self.logpath.insert(0, outputfile)

    def set_kml_path(self):
        """
        open a dialogue box to choose where we save KMl data to
        """
        outputdir = tkinter.filedialog.askdirectory()
        self.kmlpath.insert(0, outputdir)

    def save_settings(self):
        """
        get the settings from the form
        """
        if self.window.serverrunning:
            tkinter.messagebox.showwarning(
                'Network Settings',
                'cannot change settings whilst server is running')
        else:
            self.window.netsettings['Server IP'] = self.serverhost.get()
            self.window.netsettings['Server Port'] = int(self.serverport.get())
            self.window.netsettings['Remote Server IP'] = self.remotehost.get()
            self.window.netsettings['Remote Server Port'] = int(
                self.remoteport.get())
            self.window.netsettings['Log File Path'] = self.logpath.get()
            self.window.netsettings['KML File Path'] = self.kmlpath.get()
            tkinter.messagebox.showinfo(
                'Network Settings', 'Network Settings Saved', parent=self)
        self.destroy()
