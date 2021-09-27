#!coding:utf8

#author:yqq
#date:2020/9/17 0017 18:37
#description:

import requests,urllib
import json
import logging

import sys
import time
from os.path import dirname

Logging = logging.getLogger()

__all__ = ['OKEX', 'HuoBi']


OK_API_URL = 'https://www.okex.com'

if sys.platform == 'win32':  #国内
    HUOBI_API_URL = "https://api.huobi.me"
else:
    HUOBI_API_URL = "https://api.huobi.pro"
BN_API_URL ='https://api.binance.com'
ZB_API_URL = 'http://api.zb.cn/data/v1/kline?market=btc_usdt'

#K线类型1m ,5m,15m, 30m, 1h, 4h, day, week


def HttpGet(url,param = {}):
    try:
        res = requests.Session().get(url,params=param)

        # print(res.text)

        if res != None:
            return json.loads(res.text)
        else : return None 
    except Exception as e:
        print(e)
        Logging.exception(e)
        return None

#'BTC-USDT'
class OKEX(object):
    """docstring for OKEX"""
    def __init__(self):
        super(OKEX, self).__init__()
    
    #period统一接口 输入格式为1m 5m 1h
    def GetKLine(self,symbol,period,size=100):
        try:
            if period[-1:] == 'm':
                granularity = int(period[:-1])*60
            elif period[-1:] == 'h':
                granularity = int(period[:-1])*60*60
            elif period == 'day':
                granularity = 60*60*24
            params = {'granularity': granularity,'instrument_id':symbol.upper()}
            path = OK_API_URL + '/api/spot/v3/products/'+symbol.upper()+'/candles'
            # path = OK_API_URL + '/api/spot/v3/instruments/'+symbol.upper()+'/candles'
            data = HttpGet(path,params)
            if not data:
                ret = -1
            else:
                ret = data 
        except Exception as e:
            Logging.exception(e)
            ret = -1
        return ret 

    def GetRate(self,symbol,period):
        kline = self.GetKLine(symbol,period,size=100)
        kline_1m = self.GetKLine(symbol, '1m', size=5)
        if kline == -1 or kline_1m == -1:
            ret = {'OK_open':0.0,'OK_close':0.0,'OK_rate':-100.0, 'OK_volume':0.0}
        else:
            kline_last = kline[0]
            open = float(kline_last[1])
            close = float(kline_last[4])
            rate = round((close-open)/open,4)
            volume = float(kline_1m[1][5])
            ret =  {'OK_open':open,'OK_close':close,'OK_rate':rate, 'OK_volume': volume}
        return ret

    def GetTicker(self,symbol):
        try:
            params = {'instrument_id':symbol.upper()}
            path = OK_API_URL + '/api/spot/v3/instruments/'+symbol.upper()+'/ticker'
            data = HttpGet(path,params)
            ticker = data['last']
            return  float(ticker)
        except Exception as e:
            print(e)
            return -1
        

class HuoBi(object):

    def __init__(self):
        super(HuoBi, self).__init__()

    def GetTicker(self,symbol):
        try:
            params = {'symbol':symbol}
            url = HUOBI_API_URL+'/market/detail/merged'
            data = HttpGet(url,params)
            if data['status'] == 'ok':
                ticker = data['tick']['close']
                return float(ticker)
            else:
                return -1
        except Exception as e:
            print(e)
            return -1
        
        
    def GetKLine(self,symbol,period,size=200):
        #:param symbol
        #:param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
        #:param size: 可选值： [1,2000]
        #:return:
        try:
            if period[-1:] == 'm':
                period = period[:-1]+'min'
            elif period == '1h':
                period = '60min'
            elif period == 'day':
                period = '1day'
            params = {'symbol': symbol,
                    'period': period,
                    'size': size}
            url = HUOBI_API_URL+'/market/history/kline'
            data = HttpGet(url,params)
            if not data:
                klines = -1
            else:
                klines =  data.get('data', -1)
        except Exception as e:
            Logging.exception(e)
            klines = -1
        return klines
        
    def GetRate(self,symbol,period):
        kline = self.GetKLine(symbol, period,size=100)
        kline_1m = self.GetKLine(symbol, '1min', size=5)
        if kline == -1 or kline_1m == -1:
            # ret = {'HB_open':0.0,'HB_close':0.0,'HB_rate':-100.0, 'HB_volume': 0.0}
            raise Exception('get kline error')
        kline_last = kline[0]
        open = float(kline_last['open'])
        close = float(kline_last['close'])
        rate = round((close - open) / open, 4)
        volume = kline_1m[0]['amount']
        ret = {'HB_open': open, 'HB_close': close, 'HB_rate': rate, 'HB_volume': volume}
        print('========> {}'.format(ret))
        return ret


class ZB(object):
    """docstring for ZB"""
    def __init__(self):
        super(ZB, self).__init__()

    def GetKLine(self,symbol,period,size=100):
        try:
            if period[-1:] == 'm':
                period = period[:-1]+'min'
            elif period == '1h':
                period = '1hour'
            elif period == 'day':
                period = '1day'
            params = {'market': symbol,
                      'type': period,
                      'size': size}
            data = HttpGet(ZB_API_URL,params)
            if not data:
                ret = -1
            else:
                ret = data.get('data', -1)
        except Exception as e:
            Logging.error(e)
            ret = -1
        return ret

    def GetRate(self,symbol,period):
        kline = self.GetKLine(symbol,period,size=100)
        if kline == -1:
            ret = {'BN_open':0.0,'BN_close':0.0,'BN_rate':-100.0}
        else:
            kline_last = kline[-1]
            open = float(kline_last[1])
            close = float(kline_last[4])
            rate = round((close-open)/open,4)
            ret = {'BN_open':open,'BN_close':close,'BN_rate':rate}
        return ret


class BN(object):
    """docstring for BN"""
    def __init__(self):
        super(BN, self).__init__()


    def GetTicker(self,symbol):
        try:
            url = BN_API_URL+'/api/v3/ticker/price'
            params = {'symbol':symbol}
            data = HttpGet(url,params)

            return float(data['price'])
        except Exception as e:
            print(e)
            return -1
        

if __name__ == '__main__':
    ok = OKEX()
    print(ok.GetRate('BTC-USDT','5m'))
