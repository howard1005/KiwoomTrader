from kiwoom.kiwoom_real import *
from kiwoom.kiwoom_timeout import KiwoomTimeout
from interface.interface_kiwoom import InterfaceKiwoom
from interface.interface_kwos import kwosProc
from interface.interface_manager import InterfaceManager
import sys
import time
from collections import deque
import threading
from multiprocessing import Process, Manager

import pdb

class Kiwoom():
    def __init__(self):
        __test_var__ = "public"
        print("Kiwoom 클래스 입니다.")


    def run(self):
        im = InterfaceManager()
        realkiwoom = real_kiwoom(im)
        realkiwoom.start()

        ik = InterfaceKiwoom(im) # Test용
        while(1):
            ''' Do Test
            ik.send_TR(trCode='opt10004', trInput={
                "종목코드": "042670"
                #"기준일자": "20200101",
                #"수정주가구분": "1"
            })
            '''

            kwosproc = kwosProc(im)
            kwosproc.start()
            kwosproc.join()
            del kwosproc

