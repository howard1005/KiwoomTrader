from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from kiwoomOS.kwos import *
from threading import Thread
from multiprocessing import Process, Manager, Pipe
import time

class InterfaceKiwoomOS:
    def __init__(self, interface_manager):
        self.im = interface_manager
        self.manager_list = self.im.get_list()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kos = KiwoomOS(self.kiwoom)
        self.kos.addOnLogin(self.kos_onLogin)
        self.kos.addOnReceiveTr(self.kos_OnReceiveTr)
        self.kos.addOnReceiveReal(self.kos_OnReceiveReal)
        self.kos.addOnReceiveRealExt(self.kos_OnReceiveRealExt)
        self.kos.addOnAcceptedOrder(self.kos_OnAcceptedOrder)
        self.kos.addOnConcludedOrder(self.kos_OnConcludedOrder)
        self.kos.addOnReceiveBalance(self.kos_OnReceiveBalance)
        self.kos.addOnReceiveCondition(self.kos_OnReceiveCondition)
        self.kos.addOnReceiveRealCondition(self.kos_OnReceiveRealCondition)
        self.kos.addOnReceiveAccountState(self.kos_OnReceiveAccountState)

        self._state = False
        self._accounts = []
        self.kos.login()  # auto login

        self.manager_handler = Thread(target=self._thread_manager_handler, daemon=True)
        self.manager_handler.start()

        self.time = time.time()
        self.timeout_handler = Thread(target=self._thread_timeout_handler, daemon=True)
        self.timeout_handler.start()

    def _thread_timeout_handler(self):
        while (1):
            time.sleep(5)
            if time.time() - self.time >= 300:
                print("[kwos] [_thread_timeout_handler] Kiwoom Timeout!!")
                self._state = False
                self.manager_handler.join()
                QCoreApplication.quit()
                break

    def _thread_manager_handler(self):
        call_cnt = 0
        while not self._state:
            time.sleep(1)
        while self._state:
            try:
                for p in self.manager_list:
                    if p.poll():
                        self._request_task(p.recv())
                        call_cnt += 1
                        if call_cnt > 1000:
                            self.time = 0
            except Exception as ex:
                print('[kwosProcInterface] response 에러가 발생 했습니다', ex)

    def _request_task(self, task):
        # print('[kwosProcInterface] _request_task ',task)
        if task['CMD'] == 'LOGIN':
            self.kos.login()
        elif task['CMD'] == 'TR':
            for k,v in task['SET_INPUT'].items():
                self.kos.setInput(k,v)
            self.kos.requestTr(task['rqName'], task['trCode'], task['prevNext'])
        elif task['CMD'] == 'ORDER':
            task['account'] = self._accounts[0] # account는 일단 고정
            if task['type'] == 'buy':
                self.kos.sendBuyOrder(task['account'], task['itemCode'], task['quantity'], task['price'],
                                      task['priceType'])
            elif task['type'] == 'sell':
                self.kos.sendSellOrder(task['account'], task['itemCode'], task['quantity'], task['price'],
                                       task['priceType'])
            elif task['type'] == 'cancelbuy':
                self.kos.cancelBuyOrder(task['account'], task['itemCode'], task['quantity'], task['price'],
                                      task['priceType'], task['originalOrderNum'])
            elif task['type'] == 'cancelsell':
                self.kos.cancelSellOrder(task['account'], task['itemCode'], task['quantity'],
                                        task['price'], task['priceType'], task['originalOrderNum'])
            elif task['type'] == 'updatebuy':
                self.kos.updateBuyOrder(task['account'], task['itemCode'], task['quantity'], task['price'],
                                      task['priceType'], task['originalOrderNum'])
            elif task['type'] == 'updatesell':
                self.kos.updateSellOrder(task['account'], task['itemCode'], task['quantity'], task['price'],
                                      task['priceType'], task['originalOrderNum'])
        elif task['CMD'] == 'REAL':
            self.kos.addRealData(task['codelist'])

    def _response_task(self, task):
        try:
            for p in self.manager_list:
               p.send(task)
            self.time = time.time()
        except Exception as ex:
            print('[kwosProcInterface] response 에러가 발생 했습니다', ex)

    # 로그인 완료 Event
    def kos_onLogin(self, stockItemList, conditionList):
        self.writeLog('kos_onLogin()호출 - 로그인 이벤트')
        #print("conditionList : ", conditionList)
        #print("stockItemList : ", stockItemList)

        self.writeLog('로그인 상태 :', self.kos.getLoginState())
        self.writeLog('사용자 아이디 :', self.kos.getUserId())
        self.writeLog('사용자 이름 :', self.kos.getUserName())
        self.writeLog('서버구분 :', self.kos.getServerState())

        self._state = True
        self._accounts = self.kos.getAccountList()
        print("accounts", self._accounts)

    # TR수신 Event
    def kos_OnReceiveTr(self, rqName, trCode, hasNext, trData=None):
        self.writeLog('kos_OnReceiveTr() 호출 - TR데이터 수신')
        self.writeLog('rqName', rqName)
        self.writeLog('trCode', trCode)
        self.writeLog('hasNext', hasNext)

        self._response_task({
            'CMD': 'TR',
            'rqName': rqName,
            'trCode': trCode,
            'hasNext': hasNext,
            'trData': trData # TODO : 각 trCode에 따라 parsing 필요(kwos에서 해줘야함)
        })

    # 실시간 거래 데이터 수신
    def kos_OnReceiveReal(self, itemCode, sRealType, realData=None):
        #self.writeRealLog('kos_OnReceiveReal() 호출 - 실시간 데이터 수신')
        #self.writeRealLog(itemCode)
        #self.writeRealLog(realData)

        self._response_task({
            'CMD': 'REAL',
            'itemCode': itemCode,
            'sRealType': sRealType,
            'realData': realData # TODO : 각 sRealType에 따라 parsing 필요
        })

    # 기타 실시간 데이터 수신
    def kos_OnReceiveRealExt(self, itemCode, realType):
        self.writeRealLog('kos_OnReceiveRealExt() 호출 - 기타 실시간 데이터 수신')
        self.writeRealLog('realType', realType)
        if realType == '주식당일거래원':
            sellEx1 = self.kos.getRealData(itemCode, 141)
            sellEx2 = self.kos.getRealData(itemCode, 142)
            sellEx3 = self.kos.getRealData(itemCode, 143)
            self.writeRealLog(sellEx1, sellEx2, sellEx3)

    # 주문 접수 Event
    def kos_OnAcceptedOrder(self, receipt):
        self.writeRealLog('kos_OnAcceptedOrder() 호출 - 주문접수 결과')
        self.writeRealLog(receipt)

        self._response_task({
            'CMD': 'ORDER',
            'receipt': receipt
        })

    # 주문 체결 Event
    def kos_OnConcludedOrder(self, conclusion):
        self.writeRealLog('kos_OnConcludedOrder() 호출 - 주문 체결 정보')
        self.writeRealLog(conclusion)

        self._response_task({
            'CMD': 'ORDER',
            'conclusion': conclusion
        })

    # 실시간 잔고 Event
    def kos_OnReceiveBalance(self, balance):
        self.writeRealLog('kos_kos_OnReceiveBalance() 호출 - 실시간 잔고 전달')
        self.writeRealLog(balance)

        self._response_task({
            'CMD': 'ACCOUNT',
            'balance': balance
        })

    # 조건검색 종목 Event
    def kos_OnReceiveCondition(self, condition, itemList):
        self.writeLog('kos_OnReceiveCondition() 호출 - 조건검색 결과')
        self.writeLog('condition', condition)
        self.writeLog('itemList', itemList)

    # 실시간 조건검색 Event
    def kos_OnReceiveRealCondition(self, condition, strCode, type):
        self.writeRealLog('kos_OnReceiveRealCondition() 호출 - 실시간 조건 편입/이탈')
        self.writeRealLog('condition', condition)
        self.writeRealLog('type', type)
        self.writeRealLog('strCode', strCode)

    def kos_OnReceiveAccountState(self, account_state, balance_list):
        self.writeRealLog('kos_OnReceiveAccountState() 호출 - 계좌현황')
        self._response_task({
            'CMD': 'ACCOUNT',
            'account_state': account_state,
            'balance_list': balance_list
        })

    # LogListView에 로그 출력
    def writeLog(self, *log):
        logText = ''
        for i in log:
            logText += str(i) + ' '
        print('[LOG]', logText)

    # realDataListView에 실시간 로그 출력
    def writeRealLog(self, *log):
        logText = ''
        for i in log:
            logText += str(i) + ' '
        print('[REAL_LOG]', logText)


class kwosProc(Process):
    def __init__(self, interface_manager):
        super().__init__()
        self.im = interface_manager
    def run(self):
        print("kwosProc RUN")
        app = QApplication([])
        interface = InterfaceKiwoomOS(self.im)
        app.exec_()
