from  kiwoom.kiwoom_main import *

import sys
from PyQt5.QtWidgets import *


class UI_class():
    def __init__(self):
        print("UI_class 입니다.")

        #self.app = QApplication(sys.argv)  # Qt 모듈들 초기화

        self.kiwoom = Kiwoom() # Kiwoom 클래스
        self.kiwoom.run()

        #self.app.exec_()
