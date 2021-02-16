from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *
from PyQt5.QtWidgets import *

from  kiwoom.QAxwidget_kiwoom import QAxWidget_Kiwoom

from multiprocessing import Process, Manager

import sys
from config.errorCode import *
import threading
import time
import queue
import pdb

class process_Kiwoom(Process): # Process 상속
    def __init__(self, parent, args=None):
        super(process_Kiwoom, self).__init__()

        self.main = parent
        self.args = args

        print("process_Kiwoom 클래스 입니다.")

    def run(self):
        print("process_Kiwoom run")
        app = QApplication(sys.argv)
        self.QAxWidget_kiwoom = QAxWidget_Kiwoom(parent=1, args=self.args)
        self.QAxWidget_kiwoom.run()
        app.exec()

    def quit(self):
        self.QAxWidget_kiwoom.deinit_confrol()
        print("QAxWidget_kiwoom.run() 종료")
