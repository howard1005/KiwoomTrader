from queue import Queue
from threading import Thread
from multiprocessing import Process, Manager, Queue, Pipe

class InterfaceReceiver:
    def __init__(self):
        self.q1 = Manager().Queue()
        self.q2 = Manager().Queue()

    def open(self):
        return _qpipe(self.q1, self.q2), _qpipe(self.q2, self.q1)

class _qpipe:
    def __init__(self, q1, q2):
        self.q1 = q1
        self.q2 = q2

    def send(self, data):
        self.q2.put(data)

    def recv(self):
        return self.q1.get()

    def poll(self):
        return not self.q1.empty()

