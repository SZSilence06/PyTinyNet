import os
import sys
import threading
from Tkinter import *
from tkSimpleDialog import Dialog
from tkMessageBox import showinfo, showerror
import traceback

currentDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(currentDir)

from MainClient import *
from Application import *
from Model import *

_serverIp = '192.168.153.128'
_serverPort = 2500

def showError(message):
    traceback.print_stack()
    showerror(message = message)

def showInfo(message):
    showinfo(message = message)

class Window(Frame, object):
    def __init__(self, master = None):
        try:
            super(Window, self).__init__(master)
            self._app = master
            self.pack()

            self._app.registerEventHandler('show_error', self.onShowError)
            self._app.registerEventHandler('show_info', self.onShowInfo)

            self.createWidgets()
            self.registerEventHandlers()
        except Exception, e:
            self.destroy()
            traceback.print_exc(e)
            raise e

    def getApp(self):
        return self._app

    def onDestroy(self):
        self._app.unregisterEventHandler('show_error')
        self._app.unregisterEventHandler('show_info')

    def registerEventHandlers(self):
        pass

    def onShowError(self, args):
        showError(args)

    def onShowInfo(self, args):
        showInfo(args)

class MainWindow(Window):
    def createWidgets(self):
        self._frame_username = Frame(self)
        self._frame_username.pack()
        self._frame_password = Frame(self)
        self._frame_password.pack()

        self._label_username = Label(self._frame_username)
        self._label_username['text'] = 'Name'
        self._label_username.pack({'side' : 'left'})
        self._label_username['width'] = 10
        self._edit_username = Entry(self._frame_username)
        self._edit_username.pack({'side' : 'right'})

        self._label_password = Label(self._frame_password)
        self._label_password['text'] = 'Password'
        self._label_password.pack({'side' : 'left'})
        self._label_password['width'] = 10
        self._edit_password = Entry(self._frame_password)
        self._edit_password.pack({'side' : 'right'})

        self._frame_login = Frame(self)
        self._frame_login.pack()

        self._btn_login = Button(self._frame_login)
        self._btn_login['text'] = 'Login'
        self._btn_login['command'] = self.login
        self._btn_login.pack({'side': 'left'})

        self._btn_register = Button(self._frame_login)
        self._btn_register['text'] = 'Register'
        self._btn_register['command'] = self.register
        self._btn_register.pack({'side': 'right'})

    def registerEventHandlers(self):
        self._app.registerEventHandler('login_failed', self.onLoginFailed)
        self._app.registerEventHandler('login_completed', lambda args: self._app.changeWindow(ChatWindow(self._app)))
        self._app.registerEventHandler('register_completed', self.onRegisterCompleted)
        self._app.registerEventHandler('register_failed', self.onRegisterFailed)

    def onDestroy(self):
        self._app.unregisterEventHandler('login_failed')
        self._app.unregisterEventHandler('login_completed')
        self._app.unregisterEventHandler('register_completed')
        self._app.unregisterEventHandler('register_failed')

    def _task_register(self, username, password):
        try:
            client = MainClient(self._app)
            client.connect((_serverIp, _serverPort))
            request = Request()
            request['action'] = 'register'
            request['username'] =  username
            request['password'] = password
            response = client.getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self._app.sendEvent('register_failed', response['message'])
            else:
                self._app.sendEvent('register_completed', 'Successfully registered! Now please login.')
        except Exception, e:
            traceback.print_exc(e)
            self._app.sendEvent('register_failed', 'Connection failed. Check your network and retry.')
        finally:
            client.shutdown()

    def register(self):
        username = self._edit_username.get()
        password = self._edit_password.get()
        if len(username) == 0:
            showError('Please enter username')
        elif len(username) < 3:
            showError('Username should be longer than 3 characters.')
        elif len(username) > 16:
            showError('Username should not exceed 16 characters.')
        elif len(password) == 0:
            showError('Please enter password')
        elif(len(password) < 3):
            showError('Password should be longer than 3 characters.')
        elif len(password) > 16:
            showError('Password should not exceed 16 characters.')
        else:
            self._btn_register['state'] = 'disabled'
            self._btn_register['text'] = 'Registering...'
            Thread(target = self._task_register, args = (username, password)).start()
        
    def _task_login(self, username, password):
        try:
            self._app.createClient()
            client = self._app.getClient()
            client.connect((_serverIp, _serverPort))
            request = Request()
            request['action'] = 'login' 
            request['username'] = username
            request['password'] = password
            response = client.getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self._app.sendEvent('login_failed', response['message'])
                self._app.shutdownClient()
            else:
                user = User(username)
                self._app._user = user
                user._online_time = response['online_time']
                self._app.sendEvent('login_completed')
        except Exception, e:
            traceback.print_exc(e)
            self._app.sendEvent('login_failed', 'Connection failed. Check your network and retry.')
            self._app.shutdownClient()

    def login(self):
        username = self._edit_username.get()
        password = self._edit_password.get()
        if len(username) == 0:
            showError('Please enter username')
        elif len(password) == 0:
            showError('Please enter password')
        else:
            self._btn_login['state'] = 'disabled'
            self._btn_login['text'] = 'Loginning...'
            Thread(target = self._task_login, args = (username, password)).start() 

    def onLoginFailed(self, args):
        self._btn_login['state'] = 'normal'
        self._btn_login['text'] = 'Login'
        showError(args)

    def onRegisterCompleted(self, args):
        self._btn_register['state'] = 'normal'
        self._btn_register['text'] = 'Register'
        showInfo(args)

    def onRegisterFailed(self, args):
        self._btn_register['state'] = 'normal'
        self._btn_register['text'] = 'Register'
        showError(args)

class ChatWindow(Window):
    def createWidgets(self):
        user = self._app.getUser()
        online_time = user.getOnlineTime()
        self._user_label = Label(self)
        self._user_label['text'] = "User: " + user.getName() + "    Online Time: " + str(online_time) + " seconds" 
        self._user_label.grid(row=0)
        
        self._frame_top_menu = None
        self._frame_main = None

        self.doEnterHall()

        client = self._app.getClient()
        client.registerActionHandler('broadcast', self.onBroadcast)
        client.onServerCloseConnection(lambda: self._app.sendEvent('disconnected'))
        client.onDisconnected(lambda: self._app.sendEvent('disconnected'))

    def registerEventHandlers(self):
        self._app.registerEventHandler('create_room_completed', self.onCreateRoomCompleted)
        self._app.registerEventHandler('disconnected', self.onDisconnected)

    def onDestroy(self):
        self._app.getClient().unregisterActionHandler('broadcast')

    def createHallMenuBar(self):
        result = Frame(self)

        user = self._app.getUser()
        room = user.getRoom()

        self._button_channel = Button(result)
        self._button_channel['text'] = 'Room Channel'
        self._button_channel.pack({'side': 'left'})
        if room is None:
            self._button_channel['state'] = 'disabled'
        else:
            self._button_channel['command'] = self.doEnterRoom

        self._button_create_room = Button(result)
        self._button_create_room['text'] = 'Create Room'
        self._button_create_room.pack({'side': 'left'})
        self._button_create_room['command'] = self.createRoom
        if room is not None:
            self._button_create_room['state'] = 'disabled'

        self._button_enter_room = Button(result)
        self._button_enter_room['text'] = 'Enter Room'
        self._button_enter_room.pack({'side': 'left'})
        self._button_enter_room['command'] = self.enterRoom
        if room is not None:
            self._button_enter_room['state'] = 'disabled'

        self._button_logout = Button(result)
        self._button_logout['text'] = 'Logout'
        self._button_logout.pack({'side': 'left'})
        self._button_logout['command'] = self.logout
        return result
    
    def createRoomMenuBar(self):
        result = Frame(self)

        self._button_channel = Button(result)
        self._button_channel['text'] = 'World Channel'
        self._button_channel.pack({'side': 'left'})
        self._button_channel['command'] = self.doEnterHall

        self._button_exit_room = Button(result)
        self._button_exit_room['text'] = 'Exit Room'
        self._button_exit_room.pack({'side': 'left'})
        self._button_exit_room['command'] = self.exitRoom
        self._button_logout = Button(result)
        self._button_logout['text'] = 'Logout'
        self._button_logout.pack({'side': 'left'})
        self._button_logout['command'] = self.logout
        return result

    def _task_sendBroadcast(self, message):
        try:
            request = Request()
            request['action'] = 'broadcast'
            request['message'] = message
            response = self._app.getClient().getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self._app.sendEvent('show_error', response['message'])
        except Exception, e:
            traceback.print_exc(e)
            self._app.sendEvent('show_error', 'Message failed to send. Try again later.')
        
    def sendBroadcast(self):
        message = self._frame_main.getSendMessage()
        username = self._app.getUser().getName()
        self._frame_main.insertMessage(username, message)
        Thread(target = self._task_sendBroadcast, args = (message,)).start()

    def onBroadcast(self, messageObj):
        if isinstance(self._frame_main, HallFrame):
            username_from = messageObj['from']
            message = messageObj['message']
            self._frame_main.insertMessage(username_from, message)

    def _task_createRoom(self, config):
        try:
            request = Request()
            request['action'] = 'create_room'
            request['config'] = config.toDict()
            response = self._app.getClient().getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self._app.sendEvent('show_error', response['message'])
            else:
                room_info = response['room']
                room = Room()
                room.setName(room_info['name'])
                room._userList = room_info['users']
                self._app.sendEvent('create_room_completed', room)
        except Exception, e:
            traceback.print_exc(e)
            self._app.sendEvent('show_error', 'Create room failed. Try again later.')

    def createRoom(self):
        dialog = CreateRoomDialog(self)
        if dialog.isOK():
            config = dialog.getRoomConfig()
            Thread(target=self._task_createRoom, args=(config,)).start()

    def _task_enterRoom(self, roomname):
        try:
            request = Request()
            request['action'] = 'enter_room'
            request['room'] = roomname
            response = self._app.getClient().getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self._app.sendEvent('show_error', response['message'])
            else:
                room_info = response['room']
                room = Room()
                room.setName(room_info['name'])
                room._userList = room_info['users']
                self._app.sendEvent('create_room_completed', room)
        except Exception, e:
            traceback.print_exc(e)
            self._app.sendEvent('show_error', 'Enter room failed. Try again later.')

    def enterRoom(self):
        dialog = EnterRoomDialog(self)
        if dialog.isOK():
            roomname = dialog.getRoomName()
            Thread(target=self._task_enterRoom, args=(roomname,)).start()

    def _task_exitRoom(self):
        try:
            request = Request()
            request['action'] = 'exit_room'
            response = self._app.getClient().getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self._app.sendEvent('show_error', response['message'])
        except Exception, e:
            traceback.print_exc(e)
            self._app.sendEvent('show_error', 'Exit room failed. Try again later.')

    def exitRoom(self):
        self.unregisterRoomActionHandlers()
        self._app.getUser().setRoom(None)
        self.doEnterHall()
        Thread(target=self._task_exitRoom).start()

    def doEnterHall(self):
        if self._frame_top_menu is not None:
            self._frame_top_menu.destroy()
        if self._frame_main is not None:
            self._frame_main.destroy()
        self._frame_top_menu = self.createHallMenuBar()
        self._frame_top_menu.grid(row=1)
        self._frame_main = HallFrame(self)
        self._frame_main.grid(row=2)

    def doEnterRoom(self):        
        if(self._frame_top_menu):
             self._frame_top_menu.destroy()
        if(self._frame_main):
            self._frame_main.destroy()
        self._frame_main = RoomFrame(self, self._app.getUser().getRoom())
        self._frame_main.grid(row=2)
        self._frame_top_menu = self.createRoomMenuBar()
        self._frame_top_menu.grid(row=1)

    def logout(self):
        self._app.changeWindow(MainWindow(self._app))
        self._app.shutdownClient()

    def _task_sendRoomMessage(self, message):
        try:
            request = Request()
            request['action'] = 'send_room_message'
            request['message'] = message
            response = self._app.getClient().getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self._app.sendEvent('show_error', response['message'])
        except Exception, e:
            traceback.print_exc(e)
            self._app.sendEvent('show_error', 'Send message failed. Try again later.')

    def sendRoomMessage(self):
        message = self._frame_main.getSendMessage()
        username = self._app.getUser().getName()
        self._frame_main.insertMessage(username, message)
        Thread(target=self._task_sendRoomMessage, args=(message,)).start()

    def unregisterRoomActionHandlers(self):
        client = self._app.getClient()
        client.unregisterActionHandler('room_server_broadcast')
        client.unregisterActionHandler('room_user_enter')
        client.unregisterActionHandler('room_user_exit')

    def onRoomServerBroadcast(self, messageObj):
        if isinstance(self._frame_main, RoomFrame):
            self._frame_main.insertSystemMessage(messageObj['message'])
        
    def onRoomUserEnter(self, messageObj):
        user = messageObj['user']
        if isinstance(self._frame_main, RoomFrame):
            self._frame_main._list_roomusers.insert(END, user)
        self._app.getUser().getRoom().addUser(user)

    def onRoomUserExit(self, messageObj):
        user = messageObj['user']
        if isinstance(self._frame_main, RoomFrame):
            self._frame_main.removeUser(user)
        self._app.getUser().getRoom().removeUser(user)

    def onRoomReceiveMessage(self, messageObj):
        if isinstance(self._frame_main, RoomFrame):
            username_from = messageObj['from']
            message = messageObj['message']
            self._frame_main.insertMessage(username_from, message)

    def onDisconnected(self, args):
        showError('Connection was broken. Check your network.')
        self.logout()
        
    def onCreateRoomCompleted(self, args):
        self._app.getUser().setRoom(args)
        self.doEnterRoom()

class ChatMainFrame(Frame, object):
    def getChatText(self):
        return self._text_chatroom

    def getSendMessage(self):
        return self._text_edit_message.get('0.0', END)
    
    def insertMessage(self, name, message):
        self._text_chatroom['state'] = 'normal'
        self._text_chatroom.insert(INSERT, name + ":" + message)
        self._text_chatroom['state'] = 'disabled'

    def insertSystemMessage(self, message):
        self._text_chatroom['state'] = 'normal'
        self._text_chatroom.insert(INSERT, message + '\n')
        self._text_chatroom['state'] = 'disabled'

    def destroy(self):
        self.onDestroy()
        super(ChatMainFrame, self).destroy()

    def onDestroy(self):
        pass

class HallFrame(ChatMainFrame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self._text_chatroom = Text(self)
        self._text_chatroom['width'] = 60
        self._text_chatroom['height'] = 20
        self._text_chatroom.grid(row=0, column=0, columnspan=2, padx=5)
        self._text_chatroom.configure(state="disabled")

        self._text_edit_message = Text(self)
        self._text_edit_message.grid(row=1, column=0, sticky=W, padx=5)
        self._text_edit_message['height'] = 3
        self._text_edit_message['width'] = 50
        self._button_send_message = Button(self)
        self._button_send_message.grid(row=1, column=1)
        self._button_send_message['text'] = 'Send'
        self._button_send_message['command'] = master.sendBroadcast       
    
class RoomFrame(ChatMainFrame):
    def __init__(self, master, room):
        Frame.__init__(self, master)
        self._label_roomname = Label(self)
        self._label_roomname['text'] = 'Room: ' + room.getName()
        self._label_roomname.grid(row=0,column=0)
        self._text_chatroom = Text(self)
        self._text_chatroom['width'] = 50
        self._text_chatroom['height'] = 20
        self._text_chatroom.grid(row=1, column=0, padx=5, pady=5)
        self._text_chatroom.configure(state="disabled")
        self._label_roomusers = Label(self)
        self._label_roomusers['text'] = 'Room User List'
        self._label_roomusers.grid(row=0,column=1)
        self._list_roomusers = Listbox(self)
        self._list_roomusers['width'] = 12
        self._list_roomusers['height'] = 18
        self._list_roomusers.grid(row=1,column=1)
        for username in room.getUserList():
            self._list_roomusers.insert(END, username)

        self._text_edit_message = Text(self)
        self._text_edit_message.grid(row=2, column=0, sticky=W, padx=5)
        self._text_edit_message['height'] = 3
        self._text_edit_message['width'] = 50
        self._button_send_message = Button(self)
        self._button_send_message.grid(row=2, column=1)
        self._button_send_message['text'] = 'Send'
        self._button_send_message['command'] = master.sendRoomMessage

        client = self.master.getApp().getClient()
        client.registerActionHandler('room_server_broadcast', master.onRoomServerBroadcast)
        client.registerActionHandler('room_user_enter', master.onRoomUserEnter)
        client.registerActionHandler('room_user_exit', master.onRoomUserExit)
        client.registerActionHandler('room_receive_message', master.onRoomReceiveMessage)

    def removeUser(self, user):
        for index, content in enumerate(self._list_roomusers.get(0, END)):
            if content == user:
                self._list_roomusers.delete(index)
                break 
        
class MyDialog(Dialog, object):
    def body(self, master):
        self._result = False

    def apply(self):
        self._result = True

    def isOK(self):
        return self._result

class CreateRoomDialog(MyDialog):
    def body(self, master):
        super(CreateRoomDialog, self).body(master)
        self._label_roomname = Label(master)
        self._label_roomname['text'] = "Room Name"
        self._label_roomname.grid(row=0, column=0, sticky=W)
        self._entry_roomname = Entry(master)
        self._entry_roomname.grid(row=0, column=1)

    def validate(self):
        roomname = self._entry_roomname.get()
        if len(roomname) > RoomConfig.MAX_NAME_LENGTH:
            showError('Room name should not exceed ' + 
                str(RoomConfig.MAX_NAME_LENGTH) + ' characters.')
            return False
        return True

    def apply(self):
        super(CreateRoomDialog, self).apply()
        self._room_config = RoomConfig()
        self._room_config.setName(self._entry_roomname.get())

    def getRoomConfig(self):
        return self._room_config

class EnterRoomDialog(MyDialog):
    def body(self, master):
        super(EnterRoomDialog, self).body(master)
        self._label_roomlist = Label(master)
        self._label_roomlist['text'] = "Getting rooms... Please wait"
        self._label_roomlist.pack()
        self._list_room = Listbox(master)
        self._list_room.pack()
        self._roomname = None

        app = self.master.getApp()
        app.registerEventHandler('get_rooms_completed', self.onGetRoomsCompleted)
        app.registerEventHandler('get_rooms_failed', self.onGetRoomsFailed)

        Thread(target=self._task_getRooms).start()

    def validate(self):
        indices = self._list_room.curselection()
        if len(indices) == 0:
            showError('Please select a room.')
            return False
        self._roomname = self._list_room.get(indices[0])
        return True

    def apply(self):
        super(EnterRoomDialog, self).apply()

        app = self.master.getApp()
        app.unregisterEventHandler('get_rooms_completed')
        app.unregisterEventHandler('get_rooms_failed')

    def _task_getRooms(self):
        try:
            request = Request()
            request['action'] = 'get_rooms'
            response = self.master.getApp().getClient().getResponse(request)
            if(response['code'] != Code.SUCCESS):
                self.master.getApp().sendEvent('get_rooms_failed', response['message'])
            else:
                rooms = response['rooms']
                self.master.getApp().sendEvent('get_rooms_completed', rooms)
        except Exception, e:
            traceback.print_exc(e)
            self._master.getApp().sendEvent('get_rooms_failed', 'Get room list failed. Try again later.')

    def onGetRoomsCompleted(self, args):
        self._label_roomlist['text'] = 'Room List'
        for room in args:
            self._list_room.insert(END, room)

    def onGetRoomsFailed(self, args):
        self._label_roomlist['text'] = 'Room List'
        showError(args)

    def getRoomName(self):
        return self._roomname

