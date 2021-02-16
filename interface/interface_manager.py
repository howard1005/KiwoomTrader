from queue import Queue
from threading import Thread
from multiprocessing import Process, Manager, Queue, Pipe

class InterfaceManager(object):
    def __init__(self):
        _manager = Manager()
        self._list = _manager.list()
        self._semaphore = _manager.Semaphore()

    def get_list(self):
        return self._list

    def register(self, ir):
        self._semaphore.acquire()
        id = len(self._list)
        self._list.append(ir)
        self._semaphore.release()
        print("[InterfaceManager] [register] id:{}".format(id))
        return id

    def deregister(self, id):
        self._semaphore.acquire()
        del self._list[id]
        print("[InterfaceManager] [deregister] id:{}".format(id))
        self._semaphore.release()


