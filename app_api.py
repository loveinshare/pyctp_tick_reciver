from api_package import *
import time,os,queue,threading,re,datetime, pickle,sys,paramiko,json
import pandas as pd;import numpy as np


class app_ctp_mdapi(CtpMdApi):
    def __init__(self, TickQ,):
        """Constructor"""
        super(app_ctp_mdapi, self).__init__()
        self.TickQ = TickQ
    def onRtnDepthMarketData(self, data: dict):
        self.TickQ.put(data)


class app_ctp_tdapi (CtpTdApi):
    def __init__(self, order_ref):
        self.inited = None
        self.Option_ContractL = []
        self.Option_ContractL_raw = []
        self.Option_ContractL_of_exch = {
            "SHFE":[],
            "DCE":[],
            "CZCE":[], 
            "INE":[],
            "CFFEX":[],     
        }

        self.Futures_ContractL = []
        self.Futures_ContractL_raw = []
        self.Futures_ContractL_of_exch = {
            "SHFE":[],
            "DCE":[],
            "CZCE":[], 
            "INE":[],
            "CFFEX":[],     
        }
        """Constructor"""
        super(app_ctp_tdapi, self).__init__(order_ref)

    def onRspSettlementInfoConfirm(self, data: dict, error: dict, reqid: int, last: bool):
        """
        Callback of settlment info confimation.
        """
        # self.gateway.write_log("结算信息确认成功")
        print("结算信息确认成功")
        self.inited = True
        self.reqid += 1
        self.reqQryInstrument({}, self.reqid)
    def onRspQryInstrument(self, data: dict, error: dict, reqid: int, last: bool):
        if   data["ProductClass"] =="3" or data["ProductClass"]== "5":
            return
        elif data["ProductClass"] =="2":
            self.Option_ContractL_of_exch[data["ExchangeID"]].append(data["InstrumentID"])
            self.Option_ContractL.append(data["InstrumentID"])
            self.Option_ContractL_raw.append(data)
        else:
            self.Futures_ContractL_of_exch[data["ExchangeID"]].append(data["InstrumentID"])
            self.Futures_ContractL.append(data["InstrumentID"])
            self.Futures_ContractL_raw.append(data)