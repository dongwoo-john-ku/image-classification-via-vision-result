from threading import *
from socket import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PIL import Image
import time, datetime, os, sys, io
import struct
ABR_IMAGE_HEADER_SIZE = 8

class Signal(QObject):
    recv_signal = pyqtSignal(str)
    recv_image = pyqtSignal(str)
    recv_imageDir = pyqtSignal(str)
    disconn_signal = pyqtSignal()

class ClientSocket:
    def __init__(self, parent):
        self.parent = parent
        self.recv = Signal()
        self.recv.recv_signal.connect(self.parent.updateMsg)
        self.disconn = Signal()
        self.disconn.disconn_signal.connect(self.parent.updateDisconnect)
        self.bConnect = False
        self.imageData = []

    def __del__(self):
        self.stop()

    def connectServer(self, ip, port):
        self.port = port
        self.client = socket(AF_INET, SOCK_STREAM)
        try:
            self.client.connect( (ip, port) )
        except Exception as e:
            print('Connect Error : ', e)
            return False
        else:
            self.bConnect = True
            self.t = Thread(target=self.receive, args=(self.client,))
            self.t.start()
            print('Connected')

        return True

    def stop(self):
        self.bConnect = False
        if hasattr(self, 'client'):
            self.client.close()
            del(self.client)
            print('Client Stop')
            self.disconn.disconn_signal.emit()

    def receive(self, client):
        iImgChunck = 0
        iImgChunckBuffer = 0
        while self.bConnect:
            if self.port == 2005 :
                try:
                    recv = client.recv(255)
                except Exception as e:
                    print('Recv() Error :', e)
                    break
                else:
                    msg = str(recv, encoding='utf-8')
                    if msg:
                        self.recv.recv_signal.emit(msg)
                        # print('[RECV]:', msg)
            else :
                try:
                    recv = client.recv(65535)
                except Exception as e:
                    print('Recv() Error :', e)
                    break
                else:
                    lastSentence = recv[-2:]
                    if lastSentence != b'\r\n':
                        self.imageData.append(recv)
                    else:
                        print("Image Chunck Done!!!!")
                        iImgChunck += 1
                        self.imageData.append(recv)
                        imageDataAll = b''.join(self.imageData)
                        try :
                            image = Image.open(io.BytesIO(imageDataAll[21:-2]))
                        except :
                            print("err!!!!!!!!!!!!!!!!!")
                        else:
                            print("ok")
                            now = datetime.datetime.now()
                            imageSaveDir = './Imagelog/' + str(now.strftime("%H-%M-%S")) +'.bmp'
                            inspectionTime = now.strftime('%Y-%m-%d %H:%M:%S')
                            image.save(imageSaveDir)
                            image.close()

                        self.imageData = []
                        self.recv.recv_image.emit(str(inspectionTime))
                        self.recv.recv_imageDir.emit(imageSaveDir)
        self.stop()
        print("stop")

    def send(self, msg):
        if not self.bConnect:
            return
        try:
            self.client.send(msg.encode())
        except Exception as e:
            print('Send() Error : ', e)
