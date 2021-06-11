#!coding:utf8

#author:yqq
#date:2020/9/17 0017 18:37
#description:

import hashlib
import time
import requests
import sys
import os
from pprint import pprint
from os.path import dirname
sys.path.insert(0, dirname(os.path.abspath(__file__)))


class TokenCanProxy:

    # API_RUL = 'https://openapi.tokencan.net'
    API_RUL = 'https://openapi.tokencan.co'

    URI_ORDER_PLACE = '/open/api/create_order'
    URI_ORDER_CANCEL = '/open/api/cancel_order'
    URI_ORDER_CANCEL_ALL = '/open/api/cancel_order_all'
    URI_ORDER_ENTRUST = '/open/api/v2/new_order'
    URI_ORDER_INFO = '/open/api/order_info'
     
    URI_BALANCE = '/open/api/user/account'
    URI_TICKER = '/open/api/market'
    URI_GETRECORDS = '/open/api/get_records'

    def __init__(self, **kwargs):
        self.uid = kwargs.get('uid')
        self.akey = kwargs.get('akey')
        self.skey = kwargs.get('skey').encode(encoding='UTF-8')
    
    @staticmethod
    def http_post_request(url, params=None, timeout=10) :
        response = requests.post(url, params, timeout=timeout)
        if response.status_code != 200:
            raise Exception('http error code:{}'.format(response.status_code))
        json_rsp = response.json()
        return json_rsp

    @staticmethod
    def direct_http_get(url, params=None, timeout=10):
        response = requests.get(url, params, timeout=timeout)
        if response.status_code != 200:
            raise Exception('http error code:{}'.format(response.status_code))
        json_rsp = response.json()
        return json_rsp

    def _sign(self, params):
        sign = ''
        for key in sorted(params.keys()):
            sign += key + str(params[key])
       
        sign += self.skey.decode(encoding='UTF-8')
   
        return hashlib.md5(sign.encode("utf8")).hexdigest()

    def _api_key_post(self, params, api_uri, timeout=10) :

        timestamp = int(round(time.time()*1000))
       
       
        params_to_sign = {'api_key': self.akey,
                          'time': timestamp}
        params_to_sign.update(params)
       
        params_to_sign['sign'] = self._sign(params_to_sign)
        url = TokenCanProxy.API_RUL + api_uri

        rsp = TokenCanProxy.http_post_request(url, params_to_sign, timeout)
        if int(rsp['code']) != 0:
            raise Exception("code:{}, msg: {}".format(rsp['code'], rsp['msg']))
        return rsp

    def _api_key_get(self, params, api_uri, timeout=10)  :
        timestamp = int(round(time.time()*1000))
       
        params_to_sign = {'api_key': self.akey,
                          'time': timestamp}
        params_to_sign.update(params)
       
        params_to_sign['sign'] = self._sign(params_to_sign)
        url = TokenCanProxy.API_RUL + api_uri

        rsp = TokenCanProxy.direct_http_get(url, params_to_sign, timeout)
        if int(rsp['code']) != 0:
            raise Exception("code: {}, msg:{}".format(rsp['code'], rsp['msg']))
        return rsp

    def get_ticker(self, symbol, timeout=10):
        url = TokenCanProxy.API_RUL + TokenCanProxy.URI_TICKER
           
        ret = TokenCanProxy.direct_http_get(url, timeout=timeout)

        ticker = ret['data'][symbol]

        return ticker


    def get_records(self, symbol, period, timeout = 10):
        p = {'symbol': symbol, 'period': period}
        ret = self._api_key_get(p, TokenCanProxy.URI_GETRECORDS, timeout)
        return ret


    def query_balance(self, timeout=10):
        p = {}
        ret = self._api_key_get(p, TokenCanProxy.URI_BALANCE, timeout)
        acc = ret['data']['coin_list']
        return acc
         

    def query_order(self,symbol,id,timeout=10):
        p = {'symbol':symbol,'order_id':id}
        ret = self._api_key_get(p, TokenCanProxy.URI_ORDER_INFO, timeout)
        return ret

    def query_entrust_cur(self, symbol: str, count: int = 100, timeout=10):
        p = {'symbol':symbol,'pageSize':count}
       
        ret = self._api_key_get(p, TokenCanProxy.URI_ORDER_ENTRUST, timeout)
        # print(ret)
        return ret 
    
        
    def order_commit(self,symbol, side, price, amount, timeout=10):
        p = {'side':side, 'type':'1', 'volume': amount, 'price':price, 'symbol':symbol}
        ret = self._api_key_post(p, TokenCanProxy.URI_ORDER_PLACE, timeout)

        return ret 

    def order_cancel(self, symbol, id, timeout=10) :
        p = {'symbol':symbol, 'order_id':id}
        ret = self._api_key_post(p, TokenCanProxy.URI_ORDER_CANCEL, timeout)
        return ret

    def batch_order_cancel(self,symbol,timeout=10):
        p = {'symbol':symbol}
        ret = self._api_key_post(p, TokenCanProxy.URI_ORDER_CANCEL_ALL, timeout)
        return ret
    





if __name__ == '__main__':
    hc = TokenCanProxy(uid ='',
                       akey='a2db7ea089fed50d541555127d643d0a',
                       skey='6db88c3d1bdae5e3e7336a115b1272a0')
    #hc = TCClient(uid = '',akey=' 9e7fab136dd4694b531efdfddff5b48a',skey='625c9668ee53fbabe38e21786661fb9c')
    #ticker = hc.Get_ticker('btcusdt')

    ret = hc.query_balance()
    pprint(ret)
    #
    # print(ret,len(ret))
    
  
    # id = hc.order_commit(symbol='htdfusdt', side='BUY', price=0.076, amount=10, timeout= 10)

    # print(id)

    # id = '32401098'
    # oi = hc.query_order('htdfusdt', id)
    # pprint(oi)

    # os = hc.query_entrust_cur(symbol='htdfusdt', count=100, timeout=10)
    # pprint(os)

    # ret = hc.batch_order_cancel('htdfusdt')
    # print(ret)


    # klines = hc.get_records(symbol='htdfusdt', period=1440, timeout=10)
    # pprint(klines)


