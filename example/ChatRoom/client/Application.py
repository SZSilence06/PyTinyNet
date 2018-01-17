import os
import sys
import Tkinter
import tkMessageBox
import traceback

currentDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(currentDir)

from MainClient import *
from Window import *
from Model import *

Tk = Tkinter.Tk
Button = Tkinter.Button
Frame = Tkinter.Frame
Entry = Tkinter.Entry
Label = Tkinter.Label
TopLevel = Tkinter.Toplevel

showerror = tkMessageBox.showerror
showinfo = tkMessageBox.showinfo

class Application(Tk, object):
    def __init__(self):
        super(Application, self).__init__()
        
        self._current_window = None
        self._client = None
        self._user = None
        self.changeWindow(MainWindow(self))
        self.protocol("WM_DELETE_WINDOW", self.onDestroy)
        self.resizable(width=False, height=False)
        
    def getCurrentWindow(self):
        return self._current_window

    def changeWindow(self, window):
        if self._current_window:
            self._current_window.onDestroy()
            self._current_window.destroy()
        self._current_window = window

    def createClient(self):
        if self._client:
            self._client.shutdown()
        self._client = MainClient()

    def getClient(self):
        return self._client

    def getUser(self):
        return self._user

    def shutdownClient(self):
        if self._client:
            self._client.shutdown()
            self._client = None
        self._user = None

    def onDestroy(self):
        if self._client:
            self._client.shutdown()
        self.destroy()

if __name__ == '__main__':
    app = Application()
    app.mainloop()
