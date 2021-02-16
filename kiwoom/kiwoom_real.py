from PyQt5.QtWidgets import *
from kiwoom.kiwoom_data import real_data
from interface.interface_kiwoom import InterfaceKiwoom
from kiwoom.kiwoom_db import kiwoom_db
from multiprocessing import Process, Manager, Queue
from interface.interface_manager import InterfaceManager
from threading import Thread

class real_kiwoom(Process):
    def __init__(self, interface_manager):
        super().__init__()
        print("real_kiwoom 클래스 입니다.")
        self.im = interface_manager
        #self._im = InterfaceManager()
        #self._manager_list = self._im.get_list()
        self.process_stock_dict = {}
        self.qpipe_stock_dict = {}
        self.db = None

    def run(self):
        app = QApplication([])
        self.db = kiwoom_db()
        ik = InterfaceKiwoom(self.im)
        ik.onReceive()
        ik.addOnReceiveReal(self.stock_run)
        #manager_handler = Thread(target=self._thread_manager_handler, args=(ik,), daemon=True)
        #manager_handler.start()
        app.exec_()

    def stock_run(self, data):
        print("################################################################################ [real_kiwoom] [stock_run] in ################################################################################")
        print("[real_kiwoom] [stock_run] data : {}".format(data))
        sRealType = data['sRealType']
        stock_no = data['itemCode']
        realData = data['realData']
        self.db.db_insert(sRealType, stock_no, realData)

        #return
        if not stock_no in self.process_stock_dict:
            #_manager_list_len = len(self._manager_list)
            sh = stock_handle(stock_no, self.im)
            sh.start()
            self.process_stock_dict[stock_no] = sh
            #print("[real_kiwoom] [stock_run] self.process_stock_dict : {}".format(self.process_stock_dict))
            #while(len(self._manager_list) != _manager_list_len+1):
            #    print("wait to make qpipe self._manager_list : {}".format(self._manager_list))
            #self.qpipe_stock_dict[stock_no] = self._manager_list[_manager_list_len]
        #print("[real_kiwoom] qpipe_stock_dict[{}] send".format(stock_no))
        #self.qpipe_stock_dict[stock_no].send(data)
        print("################################################################################ [real_kiwoom] [stock_run] out ################################################################################")
    '''
    def _thread_manager_handler(self, ik):
        while 1:
            try:
                for p in self._manager_list:
                    if p.poll():
                        ik._send_task(p.recv())
            except Exception as ex:
                print('[real_kiwoom] response 에러가 발생 했습니다', ex)
    '''


class stock_handle(Process):
    def __init__(self, stock_no, interface_manager):
        super().__init__()
        print("stock_handle 클래스 입니다.")
        self.stock_no = stock_no
        self.im = interface_manager
        self.strategys = strategy_stock_real_kiwoom(stock_no)
        self.fid_dicts = {"주식시세": [], "주식체결": [], "주식호가잔량": [], "주문체결": []}
        self.order = None

    def run(self):
        app = QApplication([])
        ik = InterfaceKiwoom(self.im)
        self.order = stock_order(self.stock_no, ik)
        ik.onReceive()
        ik.addOnReceiveReal(self.do_strategy)
        app.exec_()

    def do_strategy(self, data):
        print("[stock_handle] [do_stategy] ({}) data : {}".format(self.stock_no, data))
        ret_dict = {"nOrderType": -1, "nQty": -1, "nPrice": -1, "call_intensity": -1}
        if data['itemCode'] == self.stock_no:
            sRealType = data['sRealType']
            realData = data['realData']
            if sRealType == "주식시세":
                self.fid_dicts["주식시세"].append(realData)
                self.strategys.strategy1(self.fid_dicts, ret_dict)  ## 알고리즘
                self.order.order_proc(ret_dict)  ## 주문
            elif sRealType == "주식체결":
                self.fid_dicts["주식체결"].append(realData)
                self.strategys.strategy1(self.fid_dicts, ret_dict)  ## 알고리즘
                self.order.order_proc(ret_dict)  ## 주문
            elif sRealType == "주식호가잔량":
                self.fid_dicts["주식호가잔량"].append(realData)
                self.strategys.strategy1(self.fid_dicts, ret_dict)  ## 알고리즘
                self.order.order_proc(ret_dict)  ## 주문
            elif sRealType == "주문체결":
                self.order.order_confirm(self.fid_dict)  ## 주문 결과 처리


##### 주문class #####
class stock_order():
    def __init__(self, stock_num, ik):
        self.ik = ik
        self.ik.addOnReceiveAccountState(self._account)
        self.stock_num = stock_num
        self.cur_state = 0 # 0:idle한 상태 1:매수중 2:매도중
        self.cur_buy_cnt = 0
        self.cur_price = 0

        self.ik.send_TR(trCode="OPW00004", trInput={
            "계좌번호": "",
            "비밀번호": "",
            "상장폐지조회구분": "0",
            "비밀번호입력매체구분": "00"
        }, rqName="__KWOS__사용자계좌현황")

        print("stock_order 클래스 입니다.")

    def _account(self, data):
        print("[stock_order] [_account]", data)
        if 'balance' in data:
            balance = data['balance']
            if balance['종목코드'][1:] == self.stock_num:
                self.cur_price = float(balance['매입단가'])
        elif 'balance_list' in data:
            balance_list = data['balance_list']
            for balance in balance_list:
                if balance['종목코드'][1:] == self.stock_num:
                    self.cur_price = float(balance['평균단가'])
                    break

    def order_proc(self, ret_dict):
        '''
           1초에 5회만 주문가능하며 그 이상 주문요청하면 에러 -308을 리턴합니다.
           00 : 지정가
           03 : 시장가
           05 : 조건부지정가
           06 : 최유리지정가
           07 : 최우선지정가
           10 : 지정가IOC
           13 : 시장가IOC
           16 : 최유리IOC
           20 : 지정가FOK
           23 : 시장가FOK
           26 : 최유리FOK
           61 : 장전시간외종가
           62 : 시간외단일가매매
           81 : 장후시간외종가
        '''

        print("[stock_order] [order_proc] self.cur_price :", self.cur_price)

        if ret_dict["nOrderType"] == 1:  # 매수
            if self.cur_buy_cnt >= 100:
                return
            self.ik.send_ORDER("buy", "0", self.stock_num, ret_dict["nQty"], ret_dict["nPrice"], "지정가")
            self.cur_buy_cnt += 1

        elif ret_dict["nOrderType"] == 2:  # 매도
            if self.cur_buy_cnt <= 0 or ret_dict["nPrice"] < self.cur_price*1.005:
                return
            self.ik.send_ORDER("sell", "0", self.stock_num, ret_dict["nQty"], ret_dict["nPrice"], "지정가")
            self.cur_buy_cnt -= 1
        elif ret_dict["nOrderType"] == 3:  # 매수정정
            pass
        elif ret_dict["nOrderType"] == 4:  # 매도정정
            pass

##### 전략들 #####
class strategy_stock_real_kiwoom():
    def __init__(self, stock_no):
        self.stock_no = stock_no
        self.cur_price = 0
        print("strategy_stock_real_kiwoom 클래스 입니다.")

    def strategy1(self, fid_dicts, ret_dict):
        # 1. 매도호가1단에서의 가격이 유지되는 구간에서 그가격 체결량과 매도호가 잔량이 줄어드는 양이 비슷하고 그 양이 크면 산다?
        # 반대로 매수호가1단에서의 가격이 유지되는 구간에서 그가격 체결량과 매수호가 잔량이 줄어드는 양이 비슷하고 그 양이 크면 판다?
        try:
            #print("[strategy1] ({}) fid_dicts : {}".format(self.stock_no, fid_dicts))
            tick_range = 7
            stock_remain_list = fid_dicts["주식호가잔량"]
            stock_remain_list_len = len(stock_remain_list)
            stock_conclusion_list = fid_dicts["주식체결"]
            stock_conclusion_list_len = len(stock_conclusion_list)
            print("[strategy1] ({}) stock_remain_list_len : {}".format(self.stock_no, stock_remain_list_len))
            print("[strategy1] ({}) stock_conclusion_list_len : {}".format(self.stock_no, stock_conclusion_list_len))

            if stock_remain_list_len < tick_range or stock_conclusion_list_len < tick_range:
                return

            price = int(stock_remain_list[stock_remain_list_len - 1]["매도호가1"][1:])
            for single_dict in stock_remain_list[(stock_remain_list_len - tick_range):]:
                if price != int(single_dict["매도호가1"][1:]):
                    return
            diff = abs(int(stock_remain_list[stock_remain_list_len - 1]["매도호가수량1"]) \
                   - int(stock_remain_list[(stock_remain_list_len - tick_range)]["매도호가수량1"]))

            cnt = 0
            for single_dict in stock_conclusion_list[(stock_conclusion_list_len - tick_range * 2):]:
                if price == int(single_dict["현재가"][1:]):
                    cnt = cnt + int(single_dict["거래량"][1:])

            print("매수 cnt {}, diff {}".format(cnt, diff))
            if cnt > 10 and abs(cnt - diff) < 10:
                print("매수!")
                ret_dict["nOrderType"] = 1
                ret_dict["nQty"] = 1
                ret_dict["nPrice"] = price
                ret_dict["call_intensity"] = 100

            price = int(stock_remain_list[stock_remain_list_len - 1]["매수호가1"][1:])
            for single_dict in stock_remain_list[(stock_remain_list_len - tick_range):]:
                if price != int(single_dict["매수호가1"][1:]):
                    return
            diff = abs(int(stock_remain_list[stock_remain_list_len - 1]["매수호가수량1"]) \
                   - int(stock_remain_list[(stock_remain_list_len - tick_range)]["매수호가수량1"]))

            cnt = 0
            for single_dict in stock_conclusion_list[(stock_conclusion_list_len - tick_range * 2):]:
                if price == int(single_dict["현재가"][1:]):
                    cnt = cnt + int(single_dict["거래량"][1:])

            print("매도 cnt {}, diff {}".format(cnt, diff))
            if cnt > 10 and abs(cnt - diff) < 10:
                print("매도!")
                ret_dict["nOrderType"] = 2
                ret_dict["nQty"] = 1
                ret_dict["nPrice"] = price
                ret_dict["call_intensity"] = 100
        except Exception as e:
            print('예외가 발생했습니다.', e)











