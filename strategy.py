import time,os,queue,threading,re,datetime, pickle,sys,paramiko,json,traceback,random
import pandas as pd;import numpy as np


from app_api import *

class aStrategy():
    # Direction 0 买 1 卖
    # offsetflag 0 开 1 平  2  3平今

    def __init__(self,global_config):
        self.global_config = global_config
        self.userid = global_config["userid"]
        self.password = global_config["password"]
        self.md_address = global_config["md_address"]
        self.td_address = global_config["td_address"]
        self.brokerid = global_config["brokerid"]
        self.auth_code = global_config["auth_code"]
        self.app_id = global_config["app_id"]
        self.order_ref = global_config["order_ref"]


        self.sleep_time = 0.01

        self.is_alive = True
        # sets
        # self.traderQ = queue.Queue()
        self.TickQ = queue.Queue()
        # self.reportQ = queue.Queue()

    def is_dirty_data(self, data):
        # 'UpdateTime': '13:49:13'
        exch = symbol_exchange_map.get(data["InstrumentID"],"")
        
        now = datetime.datetime.now()

        Time = data["UpdateTime"]
        ActionDay = data["ActionDay"]
        year = int(ActionDay[:4])
        month = int(ActionDay[4:6])
        if exch == "":
            print("exch = ''",data)
        elif exch == "DCE":
            day = datetime.datetime.now().day
        else:
            day = int(ActionDay[6:8])
        hour, minute, second = Time.split(":")
        hour = int(hour)
        minute = int(minute)
        second = int(second)
        ActionTime = datetime.datetime(year, month, day, hour, minute, second)

        delta = now - ActionTime
        if abs(delta.total_seconds()) >= 10:
            return "Tick时间与接收时间差距过大"

        if data["BidPrice1"] > 100000000 or data["AskPrice1"] > 1000000:
            return "bidPrice1 特别大"

        if data["BidPrice1"] == 0:
            return "BidPrice1为0"

        if (hour > 3 and hour < 9) or (hour > 15 and hour < 21):

            return "不在交易时间"
        return None

    def tickT(self):
        print("[start][threading] tick_Threading")
        while self.api_is_alive:
            if not self.TickQ.empty():
                data = self.TickQ.get()
                mistake = self.is_dirty_data(data)
                if mistake:
                    continue

                trading_day = data["TradingDay"]
                t_year = trading_day[:4]
                t_month = trading_day[4:6]
                t_day = trading_day[6:]

                action_day = data["ActionDay"]
                a_year = action_day[:4]
                a_month = action_day[4:6]
                a_day = action_day[6:]

                _time_str = "%s-%s-%s %s.%s" % (a_year, a_month,
                                                a_day, data["UpdateTime"], data["UpdateMillisec"])
                _time = datetime.datetime.strptime(_time_str, '%Y-%m-%d %H:%M:%S.%f')
                #_time_str = _time
                _ID = data["InstrumentID"]
                _close = data["LastPrice"]
                _bid = data["BidPrice1"]
                _bidv = data["BidVolume1"]
                _ask = data["AskPrice1"]
                _askv = data["AskVolume1"]
                _turn_over = data["Turnover"]
                _open_interest = data["OpenInterest"]
                _volume = data["Volume"]
                _averave_price = data["AveragePrice"]

                if len(_ID)>7:
                    csv_file_root = "tick/option"
                else :
                    csv_file_root = "tick/futures"
                try:
                    csv_file =csv_file_root +"/"+ "_"+_ID+"_%s_%02d_%02d_"%(t_year,int(t_month ),int(t_day))+".csv"
                except:
                    print("?????csv_file bug")
                    pass
                columns = "_time,_close,_bid,_bidv,_ask,_askv,_turn_over,_open_interest,_volume,_averave_price\r"
                
                tick_dataL = [_time,_close,_bid,_bidv,_ask,_askv,_turn_over,_open_interest,_volume,_averave_price] 
                tick_data = ",".join(map(str,tick_dataL))+"\r"

                if not os.path.exists(csv_file):
                    with open(csv_file,"w") as f:
                        f.write(columns)
                        f.write(tick_data)
                else:
                    with open(csv_file,"a") as f:
                        f.write(tick_data) 
                if random.randint(1,100) == 100:
                    print(data)
               
            else:
                time.sleep(self.sleep_time)
        print("[end][threading] tick_Threading")

    # 处理回报系统


    def Timer(self):
        self.sys_is_on = False
       
        while self.is_alive:
            now = datetime.datetime.now()
            if (now.hour >= 21 or(now.hour == 20 and now.minute >= 40) ) or (now.hour < 2 or(now.hour == 32 and now.minute < 35)) :#
                self.trading_time = "night"
            elif (now.hour >=9 or (now.hour == 8 and now.minute >45) ) and (now.hour < 15 or (now.hour == 15 and now.minute <5)): #
                self.trading_time = "day"
            else:
                self.trading_time = None
            # print(now,"    ",is_trade_time,end = "\r")
            try:
                if self.sys_is_on == False:

                    if self.trading_time == "day" or self.trading_time == "night":
                        self.api_is_alive= True
                        self.tdapi = app_ctp_tdapi(order_ref=self.order_ref+1)
                        self.tdapi.connect(self.td_address, self.userid, self.password, self.brokerid, self.auth_code,self.app_id, "")
                        Futures_ContractL_raw,Option_ContractL_raw = self.tdapi.Futures_ContractL_raw,self.tdapi.Option_ContractL_raw
                        print("len(option)",len(Option_ContractL_raw))
                        print("len(futures)",len(Futures_ContractL_raw))
                        time.sleep(10)
                       
                        self.mdapi = app_ctp_mdapi(self.TickQ)
                        self.mdapi.subscribed = [x[ 'ExchangeInstID'] for x in  (Option_ContractL_raw+Futures_ContractL_raw)]  
                        #print(self.mdapi.subscribed)
                        self.mdapi.connect(self.md_address, self.userid, self.password, self.brokerid)
                        
                        time.sleep(4)
                        self.run()
                        self.sys_is_on = True
                    elif self.trading_time == None:
                        time.sleep(1)

                elif self.sys_is_on:
                    if self.trading_time:
                        time.sleep(1)
                    elif self.trading_time == None:
                        self.close_api()
                        self.sys_is_on = False
                        print ("[Systerm][api_close!]",datetime.datetime.now())

            except:
                traceback.print_exc()
                break

    def run(self):
        t = threading.Thread(target=self.tickT)
        t.setDaemon(True)
        t.start()

        
    def close_api(self):
        self.tdapi.close()
        self.mdapi.close()
        self.api_is_alive = False

        
    def close_sys(self):
        self.is_alive = False
        self.close_api()


