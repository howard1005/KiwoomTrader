from interface.interface_kiwoom import InterfaceKiwoom
import threading
import time
import pdb

class KiwoomTimeout(threading.Thread):
    def __init__(self, interface_manager):
        super().__init__()
        print("KiwoomTimeout 클래스 입니다.")
        self.im = interface_manager
        self.time = time.time()

    def run(self):
        ik = InterfaceKiwoom(self.im)
        ik.onReceive()
        ik.addOnReceiveTr(self.set_time)
        ik.addOnAcceptedOrder(self.set_time)
        ik.addOnReceiveReal(self.set_time)
        while(1):
            time.sleep(5)
            if time.time() - self.time >= 300:
                print("Kiwoom Timeout!!")
                break
        ik.close()

    def set_time(self, data):
        #print("[KiwoomTimeout] [set_time] data : {}".format(data))
        self.time = time.time()