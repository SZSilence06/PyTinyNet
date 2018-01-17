import thread
from sqlite3 import *
import os
import sys
import traceback
    
tinyNetDir = os.path.dirname(os.path.realpath(__file__)) + "/../../.."
sys.path.append("../../,.")

from TinyNet.Logger import *

class UserDAO:
    _instance = None
    _instance_lock = thread.allocate_lock()

    @staticmethod
    def getInstance():
        if(UserDAO._instance is None):
            UserDAO._instance_lock.acquire()
            if(UserDAO._instance is None):
                UserDAO._instance = UserDAO()
            UserDAO._instance_lock.release()
        return UserDAO._instance

    def __init__(self):
        dbdir = os.path.dirname(os.path.realpath(__file__)) + "/../db/"
        dbname = 'user.db'
        try:
            self._db = connect(dbdir + dbname)
            self._db.execute('''CREATE TABLE IF NOT EXISTS user (
                    id INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    online_time INT NOT NULL
                );''')
        except Error, e:
            TN_FATAL("failed to connect to " + dbdir + dbname)
            traceback.print_exc(e)
            exit()

    def existUser(self, username):
        cursor = self._db.cursor()
        cursor.execute('SELECT * FROM user WHERE name = ?;', (username,))
        users = cursor.fetchall()
        cursor.close()
        return len(users) != 0

    def addUser(self, username, password):
        cursor = self._db.cursor()
        cursor.execute('INSERT INTO user (name, password, online_time) VALUES(?, ?, ?);', (username, password, 0))
        cursor.close()
        self._db.commit()

    def getPassword(self, username):
        cursor = self._db.cursor()
        cursor.execute('SELECT password FROM user WHERE name = ?;', (username,))
        result = cursor.fetchone()
        cursor.close()
        return result[0]

    def getOnlineTime(self, username):
        cursor = self._db.cursor()
        cursor.execute('SELECT online_time FROM user WHERE name = ?;', (username,))
        result = cursor.fetchone()
        cursor.close()
        return result[0]

    def addOnlineTime(self, username, add_time):
        online_time = self.getOnlineTime(username)
        online_time += add_time
        cursor = self._db.cursor()
        cursor.execute('UPDATE user SET online_time = ? WHERE name = ?;', (online_time, username))
        cursor.close()
        self._db.commit()




