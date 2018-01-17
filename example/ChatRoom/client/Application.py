import os
import sys
import Tkinter
import tkMessageBox
import traceback
from Queue import *

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
        self._event_handlers = {}
        self._event_queue = Queue()
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
        self._client = MainClient(self)

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

    def getEvent(self):
        if self._event_queue.empty() == False:
            event = self._event_queue.get()
            eventName = event[0]
            args = event[1]
            if eventName in self._event_handlers:
                self._event_handlers[eventName](args)
        self.after(10, self.getEvent)

    def sendEvent(self, eventName, args=None):
        event = (eventName, args)
        self._event_queue.put(event)

    def registerEventHandler(self, eventName, callback):
        self._event_handlers[eventName] = callback

    def unregisterEventHandler(self, eventName):
        if eventName in self._event_handlers:
            del self._event_handlers[eventName]

if __name__ == '__main__':
    app = Application()
    app.after(10, app.getEvent)
    app.mainloop()
