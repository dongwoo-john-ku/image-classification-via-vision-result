
from PyQt5 import uic, QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPixmap

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from pymodbus.client.sync import ModbusTcpClient
import client, socket, time, datetime, threading, os, sys, io
import numpy as np
import pandas as pd
# from ftpServer import *

sys.setrecursionlimit(5000)
form_class = uic.loadUiType("main.ui")[0]
class myWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.c = client.ClientSocket(self)
        self.c2 = client.ClientSocket(self)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.connectClicked)
        self.pushButton_2.clicked.connect(self.resetCount)
        self.pushButton_3.clicked.connect(self.countSave)
        initialTableWideget(self.tableWidget.horizontalHeader())
        self.df = self.settingModelTableWideget()
        self.label_2.setStyleSheet("color: white;" "background-color: #34465d;" "font : bold 20px")
        self.label_5.setStyleSheet("color: black;" "background-color: #bdc3c7;" "font : bold 15px")
        self.label_6.setStyleSheet("color: black;" "background-color: #bdc3c7;" "font : bold 15px")
        self.label_7.setStyleSheet("color: black;" "background-color: #bdc3c7;" "font : bold 15px")

    def __del__(self):
        self.c.stop()

    def connectClicked(self):
        if self.c.bConnect == False:
            ip = self.lineEdit.text()
            port = self.lineEdit_2.text()

            folderDir = './Datalog'
            makeDirectory(folderDir)
            imageFolderDir = './Imagelog'
            makeDirectory(imageFolderDir)

            if self.c.connectServer(ip, int(port)):
                self.pushButton.setText('접속 종료')
                self.label_13.setText('')
                self.label_4.setText('Connected')
                f = ftpThread(user='user', password='12345', dir='.')
                try:
                    f.daemon = True   # Daemon True is necessary
                    f.start()
                except:
                    print("Fail to make FTP Server")
                else:
                    print("Success to make FTP Server")

            else:
                self.c.stop()
                self.pushButton.setText('접속')
                self.label_4.setText('Disconnected')
        else:
            try:
                self.c.stop()
            except:
                print("error occur")
            finally:
                self.pushButton.setText('접속')
                self.label_4.setText('Disconnected')

    def countSave(self):
        rowCounts = self.tableWidget_2.rowCount()
        fileName = 'count_history_' + str(datetime.datetime.today().strftime("%Y%m%d_%H%M%S"))
        for rowCount in range(rowCounts):
            modelName = self.tableWidget_2.item(rowCount,0).text()
            try:
                modelCount = self.tableWidget_2.item(rowCount,2).text()
            except:
                modelCount = '0'
            else:
                modelCount = self.tableWidget_2.item(rowCount,2).text()

            logging_file_name = fileName +'.txt'
            f = open(logging_file_name, mode='a', encoding='utf-8')
            dfLogging =  modelName +', ' + modelCount + '\n'
            f.write(dfLogging)
            f.close()

        msgbox = QtWidgets.QMessageBox(self)
        message = 'please find the below file in your folder' +'\n' + fileName
        msgbox.question(self, 'Success information', message, QtWidgets.QMessageBox.Yes)


    def resetCount(self):
        rowCounts = self.tableWidget_2.rowCount()
        for rowCount in range(rowCounts) :
            self.tableWidget_2.setItem(rowCount, 2, QtWidgets.QTableWidgetItem(''))
            self.tableWidget_2.setItem(rowCount, 3, QtWidgets.QTableWidgetItem(''))
        self.label_8.setText(str(datetime.datetime.now())[:-7])

    def updateMsg(self, msg):
        msgList = list(msg[0:9])
        self.label_15.setText(str(msgList))
        detectorExpress(msgList)
        msgStr = ''.join(msgList)
        modelName, findModelRow = findModelName(msgStr, self.df)
        foundModelCount(findModelRow)
        dataLogging('./Datalog', modelName, msgStr)

    def updateDisconnect(self):
        self.pushButton.setText('접속')

    def closeEvent(self, e):
        self.c.stop()

    def settingModelTableWideget(self):
        df = pd.read_excel('setting.xlsx', header = 0)
        # print(df['model'])

        for i in range(len(df)):
            rowCount = self.tableWidget_2.rowCount()
            self.tableWidget_2.insertRow(rowCount)
            # print(df['model'][i])
            self.tableWidget_2.setItem(i, 0, QtWidgets.QTableWidgetItem(df['model'][i]))
            self.tableWidget_2.item(i, 0).setTextAlignment(Qt.AlignHCenter)
            self.tableWidget_2.setItem(i, 1, QtWidgets.QTableWidgetItem(df['pattern'][i]))
            self.tableWidget_2.item(i, 1).setTextAlignment(Qt.AlignHCenter)

        rowCount = self.tableWidget_2.rowCount()
        self.tableWidget_2.insertRow(rowCount)
        self.tableWidget_2.setItem(rowCount, 0, QtWidgets.QTableWidgetItem('unknown'))
        self.tableWidget_2.setItem(rowCount, 1, QtWidgets.QTableWidgetItem('XXXXXXXXX'))
        self.tableWidget_2.item(rowCount, 0).setTextAlignment(Qt.AlignHCenter)
        self.tableWidget_2.item(rowCount, 1).setTextAlignment(Qt.AlignHCenter)
        return df

class CustomFtpHandler(FTPHandler):
    def on_file_received(self, file):
        """Called every time a file has been succesfully received.
        "file" is the absolute name of the file just being received.
        """
        fileName = file.split('\\')[-1]
        FileFormat = fileName.split('.')[-1]
        if FileFormat == 'bmp' :
            imageReceivedFromFtp(fileName)

class ftpServerClass:
    def __init__(self, parent):
        self.parent = parent
    def ftpServerStart(self, user, password, dir):
        # Instantiate a dummy authorizer for managing 'virtual' users
        authorizer = DummyAuthorizer()

        # Define a new user having full r/w permissions and a read-only
        # anonymous user
        authorizer.add_user(user, password, dir, perm='elradfmwMT')
        authorizer.add_anonymous(os.getcwd())

        # Instantiate FTP handler class
        handler = CustomFtpHandler
        handler.authorizer = authorizer

        # Define a customized banner (string returned when client connects)
        handler.banner = "pyftpdlib based ftpd ready."

        # Specify a masquerade address and the range of ports to use for
        # passive connections.  Decomment in case you're behind a NAT.
        #handler.masquerade_address = '151.25.42.11'
        #handler.passive_ports = range(60000, 65535)

        # Instantiate FTP server class and listen on 0.0.0.0:2121
        address = ('', 21)
        server = FTPServer(address, handler)

        # set a limit for connections
        server.max_cons = 256
        server.max_cons_per_ip = 5

        # start ftp server
        server.serve_forever()

class ftpThread(threading.Thread):
    def __init__(self, user, password, dir):
        threading.Thread.__init__(self)
        self.daemon = True
        self.user = user
        self.password = password
        self.dir = dir

    def run(self):
        self.f = ftpServerClass(self)
        self.f.ftpServerStart(self.user, self.password, self.dir)

def imageReceivedFromFtp(fileName):
    pixmap = QPixmap(fileName)
    pixmap_re = pixmap.scaled(190, 190, QtCore.Qt.KeepAspectRatio)
    myWindowUi.label_13.setPixmap(pixmap_re)
    modelName = myWindowUi.label_16.text()

    savingDir = './Imagelog/' + modelName + '/'
    makeDirectory(savingDir)
    now = datetime.datetime.now()
    fileDir = savingDir + str(datetime.datetime.today().strftime("%Y%m%d_%H%M%S")) + '.bmp'
    print(fileDir)
    pixmap.save(fileDir)

def foundModelCount(findModelRow):
    try :
        currentCount = str(int(myWindowUi.tableWidget_2.item(findModelRow,2).text()) + 1)
    except :
        currentCount = '1'
    finally :
        myWindowUi.tableWidget_2.setItem(findModelRow, 2, QtWidgets.QTableWidgetItem(currentCount))
        myWindowUi.tableWidget_2.item(findModelRow, 2).setTextAlignment(Qt.AlignHCenter)
        now = datetime.datetime.now()
        cur_time = str(datetime.time(now.hour, now.minute, now.second))
        myWindowUi.tableWidget_2.setItem(findModelRow, 3, QtWidgets.QTableWidgetItem(cur_time))
        myWindowUi.tableWidget_2.item(findModelRow, 3).setTextAlignment(Qt.AlignHCenter)
        myWindowUi.tableWidget_2.viewport().update() # neccessary for updating!!!

def findModelName(msgStr, df):
    try :
        modelName = (df.loc[df['pattern'] == msgStr, ["model"]]).iloc[0,0]
    except :
        modelName = 'unkown'
        findModelRow = myWindowUi.tableWidget_2.rowCount() - 1
    else :
        findModelRow = myWindowUi.tableWidget_2.findItems(modelName, Qt.MatchExactly)[0].row()
    finally :
        myWindowUi.label_16.setText(modelName)
        myWindowUi.label_16.setStyleSheet("color: white;" "background-color: #34465d;" "font : bold 20px")
    return modelName, findModelRow


def initialTableWideget(header):
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
    header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)

def detectorExpress(msgList):
    msgListLength = len(msgList)

    for i in range(msgListLength):
        if i < 3 :
            rowNum = i
            colNum = 1
        elif i >= 3 and i < 6 :
            rowNum = i-3
            colNum = 3
        else :
            rowNum = i-6
            colNum = 5

        myWindowUi.tableWidget.setItem(rowNum, colNum, QtWidgets.QTableWidgetItem(msgList[i]))
        myWindowUi.tableWidget.item(rowNum, colNum).setTextAlignment(Qt.AlignHCenter)
        if msgList[i] == 'P':
            myWindowUi.tableWidget.item(rowNum, colNum).setBackground(QtGui.QColor(153,255,102))
        else:
            myWindowUi.tableWidget.item(rowNum, colNum).setBackground(QtGui.QColor(153,153,153))

    myWindowUi.tableWidget.viewport().update() # neccessary for updating!!!


def makeDirectory(folderDir):
    if not os.path.isdir(folderDir):
        os.mkdir(folderDir)


def dataLogging(folderDir, modelName, msgStr):
    logging_file_name = folderDir + '/' + str(datetime.datetime.today().strftime("%Y%m%d")) +'.txt'
    f = open(logging_file_name, mode='a', encoding='utf-8')
    now = datetime.datetime.now()
    cur_time = datetime.time(now.hour, now.minute, now.second)
    RF_logging = str(cur_time) + ', ' + modelName +', ' + msgStr + '\n'
    f.write(RF_logging)
    f.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindowUi = myWindow()
    myWindowUi.show()
    sys.exit(app.exec_())

    # run()
