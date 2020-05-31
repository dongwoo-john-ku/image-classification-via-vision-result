
from PyQt5 import uic, QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPixmap

import client, socket, time, datetime, threading, os, sys, io
import pandas as pd

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
        makeImageTempDir()


    def __del__(self):
        self.c.stop()

    def connectClicked(self):
        if self.c.bConnect == False:
            ip = self.lineEdit.text()
            port = self.lineEdit_2.text()

            if self.c.connectServer(ip, int(port)):
                self.pushButton.setText('접속 종료')
                self.label_13.setText('')
                self.label_4.setText('Connected')

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
        parentPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
        countLogDir = os.path.join(parentPath, 'countlog')
        fileName = str(datetime.datetime.today().strftime("%Y%m%d_%H%M%S")) +'.txt'
        countLogFileDir = os.path.join(countLogDir, fileName)

        rowCounts = self.tableWidget_2.rowCount()
        for rowCount in range(rowCounts):
            modelName = self.tableWidget_2.item(rowCount,0).text()
            try:
                modelCount = self.tableWidget_2.item(rowCount,2).text()
            except:
                modelCount = '0'
            else:
                modelCount = self.tableWidget_2.item(rowCount,2).text()

            f = open(countLogFileDir, mode='a', encoding='utf-8')
            dfLogging =  modelName +', ' + modelCount + '\n'
            f.write(dfLogging)
            f.close()

        msgbox = QtWidgets.QMessageBox(self)
        message = 'please find the below file in your "countLog" folder' +'\n' + fileName
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
        dataLogging('Datalog', modelName, msgStr)

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

def makeImageTempDir():
    parentPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
    imageTempDir = os.path.join(parentPath, 'imageTemp')
    imageLogDir = os.path.join(parentPath, 'Imagelog')
    countLogDir = os.path.join(parentPath, 'countlog')

    makeDirectory(imageTempDir)
    makeDirectory(imageLogDir)
    makeDirectory(countLogDir)

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

    parentPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
    imageTempDir = os.path.join(parentPath, 'imageTemp')
    time.sleep(3)

    try:
        tempImagefileNames = os.listdir(imageTempDir)
        FileFormat = tempImagefileNames[0].split('.')[-1]
    except :
        imageTempFileDir = 'noFile'
    else:
        if FileFormat == 'bmp' :
            imageTempFileDir = os.path.join(imageTempDir, tempImagefileNames[0])
            print(imageTempFileDir)
        else:
            imageTempFileDir = 'noImg'
    finally:
        imageReceivedFromCamera(imageTempFileDir, imageTempDir)

def imageReceivedFromCamera(fileName, imageTempDir):
    modelName = myWindowUi.label_16.text()
    if fileName == 'noFile' :
        myWindowUi.label_13.setText("카메라에서 저장된 파일이 없습니다.")
    elif fileName == 'noImg' :
        myWindowUi.label_13.setText("해당폴더의 저장된 파일의 형식이 bmp 가 아닙니다.")
        os.remove(fileName)
    else:
        pixmap = QPixmap(fileName)
        pixmap_re = pixmap.scaled(190, 190, QtCore.Qt.KeepAspectRatio)
        myWindowUi.label_13.setPixmap(pixmap_re)
        parentPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
        savingDir = os.path.join(parentPath, 'Imagelog', modelName)
        makeDirectory(savingDir)
        now = datetime.datetime.now()
        fileDir = savingDir + '/' + str(datetime.datetime.today().strftime("%Y%m%d_%H%M%S")) + '.bmp'
        print(fileDir)
        pixmap.save(fileDir)

        filelist = [ f for f in os.listdir(imageTempDir) ]
        for file in filelist:
            deleteFilePath = os.path.join(imageTempDir, file)
            os.remove(deleteFilePath)

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
    parentPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
    savingDir = os.path.join(parentPath, folderDir)
    makeDirectory(savingDir)
    logging_file_name = savingDir + '/' + str(datetime.datetime.today().strftime("%Y%m%d")) +'.txt'
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
