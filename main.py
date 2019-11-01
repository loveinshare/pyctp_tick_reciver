import time,os,queue,threading,re,datetime, pickle,sys,paramiko,json,traceback
import pandas as pd;import numpy as np
from untraced import *

from app_api import *
from strategy import *

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument("-o", type=int, default=1)
    parser.add_argument("-w", type=int, default=0)
    parser.add_argument("-t", type=int, default=0)
    args = parser.parse_args()
    way = args.w
    order_ref = args.o
    tick_bar = args.t
    print(args)
    global_config = {
        "userid" :userid,
        "password":password,
        "md_address" : md_address,
        "td_address" : td_address,
        "brokerid" : brokerid,
        "auth_code" : auth_code,
        "app_id" :app_id,
        "order_ref" : order_ref,
    }
trader = aStrategy(global_config )
try:
    trader.Timer()
except:
    traceback. print_exc()
    print("except!")
   



    