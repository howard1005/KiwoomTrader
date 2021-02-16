from queue import Queue
from threading import Thread
from multiprocessing import Process, Manager, Pipe
from interface.interface_receiver import InterfaceReceiver

class InterfaceKiwoom:
    def __init__(self, interface_manager):
        self.im = interface_manager
        (self.c, self.p) = InterfaceReceiver().open()
        self.id = self.im.register(self.p)

        self._TR_observer = []
        self._REAL_observer = []
        self._ORDER_observer = []
        self._ACCOUNT_observer = []

    def close(self):
        self.im.deregister(self.id)

    def onReceive(self):
        manager_hadler = Thread(target=self._thread_manager_hadler, daemon=True)
        manager_hadler.start()

    def _thread_manager_hadler(self):
        while 1:
            try:
                self._receive_task(self.c.recv())
            except Exception as ex:
                print('[InterfaceKiwoom] response 에러가 발생 했습니다', ex)

    def _receive_task(self, task):
        print("[InterfaceKiwoom] [_receive_task] id : {} task : {}\n".format(self.id, task))
        if task['CMD'] == 'TR':
            for event_func in self._TR_observer:
                event_func(task)
        elif task['CMD'] == 'REAL':
            for event_func in self._REAL_observer:
                event_func(task)
        elif task['CMD'] == 'ORDER':
            for event_func in self._ORDER_observer:
                event_func(task)
        elif task['CMD'] == 'ACCOUNT':
            for event_func in self._ACCOUNT_observer:
                event_func(task)

    def _send_task(self, task):
        self.c.send(task)

    def send_TR(self, trCode, trInput, rqName='sendTR', prevNext=0):
        self._send_task({
            'CMD':'TR',
            'SET_INPUT':trInput,
            'rqName':rqName,
            'trCode':trCode,
            'prevNext':prevNext
        })

    def send_REAL(self, codelist):
        self._send_task({
            'CMD':'REAL',
            'codelist':codelist
        })

    def send_ORDER(self, type, account, itemCode, quantity, price, priceType):
        self._send_task({
            'CMD':'ORDER',
            'type':type,
            'account':account,
            'itemCode': itemCode,
            'quantity': quantity,
            'price': price,
            'priceType': priceType
        })

    # Add/Remove Event
    def addOnReceiveTr(self, func):
        if func not in self._TR_observer:
            self._TR_observer.append(func)

    def removeOnReceiveTr(self, func):
        if func in self._TR_observer:
            self._TR_observer.remove(func)

    def addOnReceiveReal(self, func):
        if func not in self._REAL_observer:
            self._REAL_observer.append(func)

    def removeOnReceiveReal(self, func):
        if func in self._REAL_observer:
            self._REAL_observer.remove(func)

    def addOnAcceptedOrder(self, func):
        if func not in self._ORDER_observer:
            self._ORDER_observer.append(func)

    def removeOnAcceptedOrder(self, func):
        if func in self._ORDER_observer:
            self._ORDER_observer.remove(func)

    def addOnReceiveAccountState(self, func):
        if func not in self._ACCOUNT_observer:
            self._ACCOUNT_observer.append(func)

    def removeOnReceiveAccountState(self, func):
        if func in self._ACCOUNT_observer:
            self._ACCOUNT_observer.remove(func)
