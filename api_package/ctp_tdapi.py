from .vnpy_envi import *
from datetime import datetime


class CtpTdApi(TdApi):
    """"""

    def __init__(self,order_ref=777):
        """Constructor"""
        super(CtpTdApi, self).__init__()

        self.reqid = 0
        self.order_ref = order_ref
        print("init order_ref",self.order_ref)
        self.connect_status = False
        self.login_status = False
        self.auth_staus = False
        self.login_failed = False

        self.userid = ""
        self.password = ""
        self.brokerid = 0
        self.auth_code = ""
        self.product_info = ""

        self.frontid = 0
        self.sessionid = 0

        self.order_data = []
        self.trade_data = []
        self.positions = {}
        self.sysid_orderid_map = {}

        self.contractL = []
        self.contractL_raw = []
        self.contractL_of_exch = {
            "SHFE":[],
            "DCE":[],
            "CZCE":[], 
            "INE":[],
            "CFFEX":[],     
        }

    def onFrontConnected(self):
        """"""
        self.connect_status = True
        # self.gateway.write_log("交易连接成功")
        print("交易连接成功     ",datetime.now())
        if self.auth_code:
            self.authenticate()
        else:
            self.login()

    def onFrontDisconnected(self, reason: int):
        """"""
        self.connect_status = False
        self.login_status = False
        # self.gateway.write_log(f"交易连接断开，原因{reason}")
        print(f"交易连接断开，原因{reason}")

    def onRspAuthenticate(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error['ErrorID']:
            self.authStatus = True
            print("交易授权验证成功")
            self.login()
        else:
            #self.gateway.write_error("交易授权验证失败", error)
            print("交易授权验证失败")

    def onRspUserLogin(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        if not error["ErrorID"]:
            self.frontid = data["FrontID"]
            self.sessionid = data["SessionID"]
            self.login_status = True
            # self.gateway.write_log("交易登录成功")
            print("交易登录成功")
            # Confirm settelment
            req = {
                "BrokerID": self.brokerid,
                "InvestorID": self.userid
            }
            self.reqid += 1
            self.reqSettlementInfoConfirm(req, self.reqid)
        else:
            self.login_failed = True

            #self.gateway.write_error("交易登录失败", error)
            print("交易登录失败")

    def onRspOrderInsert(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        print("onRspOrderInsert==================================")
        #print(data)
        # order_ref = data["OrderRef"]
        # orderid = f"{self.frontid}.{self.sessionid}.{order_ref}"
        # print("duanduanduan")
        # symbol = data["InstrumentID"]
        # #exchange = symbol_exchange_map[symbol]

        # order = OrderData(
        #     symbol=symbol,
        #     exchange=exchange,
        #     orderid=orderid,
        #     direction=DIRECTION_CTP2VT[data["Direction"]],
        #     offset=OFFSET_CTP2VT[data["CombOffsetFlag"]],
        #     price=data["LimitPrice"],
        #     volume=data["VolumeTotalOriginal"],
        #     status=Status.REJECTED,
        #     # gateway_name=self.gateway_name
        # )
        # self.gateway.on_order(order)

        #self.gateway.write_error("交易委托失败", error)
        print("\n交易委托失败", data,error)

    def onRspOrderAction(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        #self.gateway.write_error("交易撤单失败", error)
        print("\n交易撤单失败",data, error)

    def onRspQueryMaxOrderVolume(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        pass

    def onRspSettlementInfoConfirm(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback of settlment info confimation.
        """
        # self.gateway.write_log("结算信息确认成功")
        print("结算信息确认成功")
        self.reqid += 1
        self.reqQryInstrument({}, self.reqid)

    def onRspQryInvestorPosition(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        print(data)
        if not data:
            return

        if 0:
            # Get buffered position object
            key = f"{data['InstrumentID'], data['PosiDirection']}"
            position = self.positions.get(key, None)
            if not position:
                position = PositionData(
                    symbol=data["InstrumentID"],
                    exchange=symbol_exchange_map[data["InstrumentID"]],
                    direction=DIRECTION_CTP2VT[data["PosiDirection"]],
                    # gateway_name=self.gateway_name
                )
                self.positions[key] = position

            # For SHFE position data update
            if position.exchange == Exchange.SHFE:
                if data["YdPosition"] and not data["TodayPosition"]:
                    position.yd_volume = data["Position"]
            # For other exchange position data update
            else:
                position.yd_volume = data["Position"] - data["TodayPosition"]

            # Calculate previous position cost
            cost = position.price * position.volume

            # Update new position volume
            position.volume += data["Position"]
            position.pnl += data["PositionProfit"]

            # Calculate average position price
            if position.volume:
                cost += data["PositionCost"]
                position.price = cost / position.volume

            # Get frozen volume
            if position.direction == Direction.LONG:
                position.frozen += data["ShortFrozen"]
            else:
                position.frozen += data["LongFrozen"]

            if last:
                for position in self.positions.values():
                    pass
                    # self.gateway.on_position(position)

                self.positions.clear()

    def onRspQryTradingAccount(self, data: dict, error: dict, reqid: int, last: bool):
        """"""
        account = AccountData(
            accountid=data["AccountID"],
            balance=data["Balance"],
            frozen=data["FrozenMargin"] +
            data["FrozenCash"] + data["FrozenCommission"],
            # gateway_name=self.gateway_name
        )
        account.available = data["Available"]

        # self.gateway.on_account(account)
    
    def onRspQryInstrument(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback of instrument query.
        """
        
        print(data["ExchangeID"])
        self.contractL_of_exch[data["ExchangeID"]].append(data["InstrumentID"])
        self.contractL.append(data["InstrumentID"])
        self.contractL_raw.append(data)
        
        # {'InstrumentID': 'al1907',
        #  'ExchangeID': 'SHFE',
        #   'InstrumentName': '铝1907',
        #    'ExchangeInstID': 'al1907',
        #     'ProductID': 'al',
        #      'ProductClass': '1',
        #       'DeliveryYear': 2019,
        #        'DeliveryMonth': 7,
        #         'MaxMarketOrderVolume': 30,
        #          'MinMarketOrderVolume': 1,
        #           'MaxLimitOrderVolume': 500,
        #            'MinLimitOrderVolume': 1,
        #             'VolumeMultiple': 5,
        #              'PriceTick': 5.0,
        #               'CreateDate': '20180613',
        #                'OpenDate': '20180717',
        #                 'ExpireDate': '20190715',
        #                  'StartDelivDate': '20190716',
        #                   'EndDelivDate': '20190722',
        #                    'InstLifePhase': '1',
        #                     'IsTrading': 1,
        #                      'PositionType': '2',
        #                       'PositionDateType': '1',
        #                        'LongMarginRatio': 0.1,
        #                         'ShortMarginRatio': 0.1,
        #                          'MaxMarginSideAlgorithm': '1',
        #                           'UnderlyingInstrID': '',
        #                            'StrikePrice': 0.0,
        #                             'OptionsType': '\x00',
        #                                  'UnderlyingMultiple': 0.0,
        #                                   'CombinationType': '0'}
        
        
        #print(data["InstrumentID"])
        # product = PRODUCT_CTP2VT.get(data["ProductClass"], None)
        # if not product:
        #     return

        # contract = ContractData(
        #     symbol=data["InstrumentID"],
        #     exchange=EXCHANGE_CTP2VT[data["ExchangeID"]],
        #     name=data["InstrumentName"],
        #     product=product,
        #     size=data["VolumeMultiple"],
        #     pricetick=data["PriceTick"],
        #     option_underlying=data["UnderlyingInstrID"],
        #     option_type=OPTIONTYPE_CTP2VT.get(data["OptionsType"], None),
        #     option_strike=data["StrikePrice"],
        #     option_expiry=datetime.strptime(data["ExpireDate"], "%Y%m%d"),
        #     # gateway_name=self.gateway_name
        # )

        # # self.gateway.on_contract(contract)

        # symbol_exchange_map[contract.symbol] = contract.exchange
        # symbol_name_map[contract.symbol] = contract.name
        # symbol_size_map[contract.symbol] = contract.size

        # if last:
        #     # self.gateway.write_log("合约信息查询成功")
        #     print("合约信息查询成功")
        #     for data in self.order_data:
        #         self.onRtnOrder(data)
        #     self.order_data.clear()

        #     for data in self.trade_data:
        #         self.onRtnTrade(data)
        #     self.trade_data.clear()

    def onRtnOrder(self, data: dict):
        """
        Callback of order status update.
        """
        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map.get(symbol, "")
        if not exchange:
            self.order_data.append(data)
            return

        frontid = data["FrontID"]
        sessionid = data["SessionID"]
        order_ref = data["OrderRef"]
        orderid = f"{frontid}.{sessionid}.{order_ref}"

        order = OrderData(
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT[data["CombOffsetFlag"]],
            price=data["LimitPrice"],
            volume=data["VolumeTotalOriginal"],
            traded=data["VolumeTraded"],
            status=STATUS_CTP2VT[data["OrderStatus"]],
            time=data["InsertTime"],
            gateway_name=self.gateway_name
        )
        # self.gateway.on_order(order)

        self.sysid_orderid_map[data["OrderSysID"]] = orderid

    def onRtnTrade(self, data: dict):
        """
        Callback of trade status update.
        """
        symbol = data["InstrumentID"]
        exchange = symbol_exchange_map.get(symbol, "")
        if not exchange:
            self.trade_data.append(data)
            return

        orderid = self.sysid_orderid_map[data["OrderSysID"]]

        trade = TradeData(
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            tradeid=data["TradeID"],
            direction=DIRECTION_CTP2VT[data["Direction"]],
            offset=OFFSET_CTP2VT[data["OffsetFlag"]],
            price=data["Price"],
            volume=data["Volume"],
            time=data["TradeTime"],
            # gateway_name=self.gateway_name
        )
        # self.gateway.on_trade(trade)

    # def connect(self, address: str, userid: str, password: str, brokerid: int, auth_code: str, product_info: str):
    #     """
    #     Start connection to server.
    #     """
    #     self.userid = userid
    #     self.password = password
    #     self.brokerid = brokerid
    #     self.auth_code = auth_code
    #     self.product_info = product_info

    #     if not self.connect_status:
    #         #path = get_folder_path(self.gateway_name.lower())
    #         self.createFtdcTraderApi("tempPath" + "\\Td")

    #         self.subscribePrivateTopic(0)
    #         self.subscribePublicTopic(0)

    #         self.registerFront(address)
    #         self.init()
    #     else:
    #         self.authenticate()

    # def authenticate(self):
    #     """
    #     Authenticate with auth_code and product_info.
    #     """
    #     req = {
    #         "UserID": self.userid,
    #         "BrokerID": self.brokerid,
    #         "AuthCode": self.auth_code,
    #         "ProductInfo": self.product_info
    #     }

    #     self.reqid += 1
    #     self.reqAuthenticate(req, self.reqid)
    def connect(self,address: str,userid: str,password: str,brokerid: int, auth_code: str,appid: str, product_info):
        """
        Start connection to server.
        """
        self.userid = userid
        self.password = password
        self.brokerid = brokerid
        self.auth_code = auth_code
        self.appid = appid
        self.product_info = product_info

        if not self.connect_status:
            #path = get_folder_path(self.gateway_name.lower())
            self.createFtdcTraderApi("tempPath" + "\\Td")

            # self.subscribePrivateTopic(0)
            # self.subscribePublicTopic(0)

            self.registerFront(address)
            self.init()

            self.connect_status = True
        else:
            self.authenticate()

    def authenticate(self):
        """
        Authenticate with auth_code and appid.
        """
        req = {
            "UserID": self.userid,
            "BrokerID": self.brokerid,
            "AuthCode": self.auth_code,
            "AppID": self.appid
        } 

        self.reqid += 1
        self.reqAuthenticate(req, self.reqid)

    def login(self):
        """
        Login onto server.
        """
        if self.login_failed:
            return

        req = {
            "UserID": self.userid,
            "Password": self.password,
            "BrokerID": self.brokerid
        }

        self.reqid += 1
        self.reqUserLogin(req, self.reqid)

    def send_order(self, req: OrderRequest):
        """
        Send new order.
        """
        self.order_ref += 1

        ctp_req = {
            "InstrumentID": req.symbol,
            "LimitPrice": req.price,
            "VolumeTotalOriginal": int(req.volume),
            "OrderPriceType": PRICETYPE_VT2CTP.get(req.price_type, ""),
            "Direction": DIRECTION_VT2CTP.get(req.direction, ""),
            "CombOffsetFlag": OFFSET_VT2CTP.get(req.offset, ""),
            "OrderRef": str(self.order_ref),
            "InvestorID": self.userid,
            "UserID": self.userid,
            "BrokerID": self.brokerid,
            "CombHedgeFlag": THOST_FTDC_HF_Speculation,
            "ContingentCondition": THOST_FTDC_CC_Immediately,
            "ForceCloseReason": THOST_FTDC_FCC_NotForceClose,
            "IsAutoSuspend": 0,
            "TimeCondition": THOST_FTDC_TC_GFD,
            "VolumeCondition": THOST_FTDC_VC_AV,
            "MinVolume": 1,
            "ExchangeID":req.exch,

        }

        if req.price_type == PriceType.FAK:
            ctp_req["OrderPriceType"] = THOST_FTDC_OPT_LimitPrice
            ctp_req["TimeCondition"] = THOST_FTDC_TC_IOC
            ctp_req["VolumeCondition"] = THOST_FTDC_VC_AV
        elif req.price_type == PriceType.FOK:
            ctp_req["OrderPriceType"] = THOST_FTDC_OPT_LimitPrice
            ctp_req["TimeCondition"] = THOST_FTDC_TC_IOC
            ctp_req["VolumeCondition"] = THOST_FTDC_VC_CV
        #print("ctp_req",ctp_req)
        self.reqid += 1
        self.reqOrderInsert(ctp_req, self.reqid)

        orderid = f"{self.frontid}.{self.sessionid}.{self.order_ref}"
        #order = req.create_order_data(orderid, self.gateway_name)
        # self.gateway.on_order(order)

        return self.order_ref,self.reqid  # order.vt_orderid

    def cancel_order(self, req: CancelRequest):
        """
        Cancel existing order.
        """
        #frontid, sessionid, order_ref = req.orderid.split(".")

        ctp_req = {
            "InstrumentID": req.symbol,
            "ExchangeID": req.exchange,
            "OrderRef": str(req.order_ref),
            "FrontID": int(req.frontid),
            "SessionID": int(req.sessionid),
            "ActionFlag": THOST_FTDC_AF_Delete,
            "BrokerID": self.brokerid,
            "InvestorID": self.userid,
            
        }
        #print("cancel_order req:",ctp_req)
        self.reqid += 1
        self.reqOrderAction(ctp_req, self.reqid)

    def query_account(self):
        """
        Query account balance data.
        """
        self.reqid += 1
        self.reqQryTradingAccount({}, self.reqid)

    def query_position(self):
        """
        Query position holding data.
        """
        # if not symbol_exchange_map:
        #     return

        req = {
            "BrokerID": self.brokerid,
            "InvestorID": self.userid
        }

        self.reqid += 1
        self.reqQryInvestorPosition(req, self.reqid)

    def close(self):
        """"""
        if self.connect_status:
            self.exit()
    def onRspQryProduct(self,data,*arg):
        print(data)
        print(data.__dict__)
        print(arg)

class myOrderRequest():
    def __init__(self, symbol, price, volume, price_type, direction, offset,exch):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.price_type = price_type
        self.direction = direction
        self.offset = offset
        self.exch = exch
class myCancelRequest():
    def __init__(self,symbol,exchange,order_ref,frontid,sessionid):
        self.symbol = symbol
        self.exchange = exchange
        self.order_ref = order_ref
        self.frontid = frontid
        self.sessionid =  sessionid
        

if __name__ == "__main__":
    # 测试能否挂单
    api = CtpTdApi()
    # def connect(self, address: str, userid: str, password: str, brokerid: int, auth_code: str, product_info: str):
    address = 'tcp://180.168.146.187:10010'
    userid = "115177"
    password = "asdfasdf"
    brokerid = "9999"
    api.connect(address, userid, password, brokerid, "", "")
    import time
    time.sleep(3)

    #查询全部合约
    #api.reqQryInstrument({}, api.reqid)  


    r = api.reqQryOrder({}, api.reqid)
    print(r)
    time.sleep(20)