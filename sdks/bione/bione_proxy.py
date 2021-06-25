#!coding:utf8

#author:yqq
#date:2021/06/15
#description:

import hashlib
import time
import requests
import sys
import hashlib, hmac
import os
from pprint import pprint
from os.path import dirname
sys.path.insert(0, dirname(os.path.abspath(__file__)))
from urllib.parse import urlencode
import json


class BioneProxy:

    # API_RUL = 'https://openapi.tokencan.net'
    API_RUL = 'https://openapi.bione.pro'

    URI_NEW_ORDER = '/sapi/v1/order' # 创建新订单
    URI_ORDER_CANCEL = '/sapi/v1/cancel' # 撤销订单
    URI_ORDER_CANCEL_ALL = '/sapi/v1/batchCancel' # 批量撤单
    URI_ORDER_INFO = '/sapi/v1/order' # 订单查询

    URI_ACCOUNT = '/sapi/v1/account'  # 账户信息
    URI_TICKER = '/sapi/v1/ticker'  # 行情
    URI_CURRENT_ORDERS = '/sapi/v1/openOrders' # 当前订单
    URI_PING = '/sapi/v1/ping'
    URI_DEPTH = '/sapi/v1/depth'
    URI_KLINES = '/sapi/v1/klines'

    def __init__(self, **kwargs):
        self.uid = kwargs.get('uid')
        self.akey = kwargs.get('akey')
        self.skey = kwargs.get('skey').encode(encoding='UTF-8')

    @staticmethod
    def http_post_request(url, params=None, timeout=10, headers=None) :
        if headers is None:
            response = requests.post(url, data=params, timeout=timeout)
        else:
            response = requests.post(url, data=params, timeout=timeout, headers=headers)
        if response.status_code != 200:
            print(response.text)
            raise Exception('http error code:{}'.format(response.status_code))
        json_rsp = response.json()
        return json_rsp

    @staticmethod
    def direct_http_get(url, params=None, timeout=10, headers=None):
        if headers is None:
            response = requests.get(url, params, timeout=timeout)
        else:
            response = requests.get(url, params, timeout=timeout, headers=headers)

        if response.status_code != 200:
            raise Exception('http error code:{}'.format(response.status_code))
        json_rsp = response.json()
        return json_rsp

    # def _sign(self, params):
    #     sign = ''
    #     for key in sorted(params.keys()):
    #         sign += key + str(params[key])
    #
    #     sign += self.skey.decode(encoding='UTF-8')
    #
    #     return hashlib.md5(sign.encode("utf8")).hexdigest()

    def _api_key_post(self, params, api_uri, timeout=10) :

        timestamp = int(round(time.time()*1000))
        #

        data = json.dumps(params, sort_keys=True, separators=(',', ':'))
        sign_msg = str(timestamp)+'POST' + api_uri + data
        sig = hmac.new(self.skey, msg=sign_msg.encode(), digestmod=hashlib.sha256)
        # print(sig.hexdigest())

        headers = {
            'X-CH-APIKEY': '{}'.format(self.akey),
            'X-CH-TS': '{}'.format(timestamp),
            'Content-Type': 'application/json',
            'X-CH-SIGN': '{}'.format(sig.hexdigest())
        }

        url = self.API_RUL + api_uri
        # params 必须和 上面签名的 data 是一样的 , 所以直接传递即可
        rsp = self.http_post_request(url, data, timeout, headers)
        if 'code' in rsp and int(rsp['code']) != 0:
            raise Exception("code:{}, msg: {}".format(rsp['code'], rsp['msg']))
        return rsp


    def _api_key_get(self, params, api_uri, timeout=10)  :
        timestamp = int(round(time.time()*1000))
        # jstr_params = json.dumps(params, sort_keys=True, separators=(',', ':'))
        query_str = urlencode(query=params)
        if len(query_str) == 0:
            sign_msg = str(timestamp) + 'GET' + api_uri
        else:
            sign_msg = str(timestamp) + 'GET' + api_uri + '?' + query_str

        # print('sign_msg = {}'.format(sign_msg))
        sig = hmac.new(self.skey, msg=sign_msg.encode(), digestmod=hashlib.sha256)
        # print(sig.hexdigest())

        headers = {
            'X-CH-APIKEY': '{}'.format(self.akey),
            'X-CH-TS': '{}'.format(timestamp),
            'Content-Type': 'application/json',
            'X-CH-SIGN': '{}'.format(sig.hexdigest())
        }

        url = self.API_RUL + api_uri + '?' + query_str
        # print(url)

        rsp = self.direct_http_get(url, params=None, timeout=timeout, headers=headers)
        # print(rsp)
        if 'code' in rsp and int(rsp['code']) != 0:
            raise Exception("code: {}, msg:{}".format(rsp['code'], rsp['msg']))
        return rsp

    # OK
    def get_ticker(self, symbol, timeout=10):
        url = self.API_RUL + self.URI_TICKER + '?symbol=' + symbol
        # print(url)

        ret = self.direct_http_get(url, timeout=timeout)
        return ret


    # OK
    # 获取k线
    def get_kline(self, symbol, interval, limit=100, timeout = 10):
        """
        interval:   1min,5min,15min,30min,60min,1day,1week,1month
        """
        p = {'symbol': symbol, 'interval': interval, 'limit':limit}
        ret = self._api_key_get(p, self.URI_KLINES, timeout)
        # print("ret===>{}".format(ret))
        return ret


    # OK
    def query_balance(self, timeout=10):
        p = {}
        ret = self._api_key_get(p, self.URI_ACCOUNT, timeout)
        acc = ret['balances']
        return acc

    # Ok
    def query_order(self,symbol, id, timeout=10):
        p = {'orderId':id, 'symbol':symbol}
        ret = self._api_key_get(p, self.URI_ORDER_INFO, timeout)
        return ret

    # Ok
    def get_cur_orders(self, symbol, limit=100, timeout=10):
        p = {'limit': limit, 'symbol':symbol}
        ret = self._api_key_get(p, self.URI_CURRENT_ORDERS, timeout)
        return ret


    # OK
    def ping(self, timeout=10):
        url = self.API_RUL + self.URI_PING
        ret = self.direct_http_get(url, timeout=timeout)
        return ret


    # ok
    def depth(self, symbol, limit=100, timeout=10):
        url = self.API_RUL + self.URI_DEPTH
        p = {'limit':limit, 'symbol': symbol}
        ret = self.direct_http_get(url,  p, timeout=timeout)
        return ret


    # Ok
    def commit_order(self,symbol, side, price, volume, timeout=10):
        p = {'side':side, 'type':'LIMIT', 'volume': volume, 'price':price, 'symbol':symbol}
        ret = self._api_key_post(p, self.URI_NEW_ORDER, timeout)

        return ret


    # Ok
    def cancel_order(self, symbol, id, timeout=10) :
        p = {'symbol':symbol, 'orderId':id}
        ret = self._api_key_post(p, self.URI_ORDER_CANCEL, timeout)
        return ret

    # OK
    def batch_order_cancel(self,symbol, ids, timeout=10):
        p = {'symbol':symbol, 'orderIds': ids}
        ret = self._api_key_post(p, self.URI_ORDER_CANCEL_ALL, timeout)
        return ret




if __name__ == '__main__':


    import json

    # print(json.dumps(j, sort_keys=True, separators=(',',':')))

    bione = BioneProxy(uid ='',
                       akey='bf1d0ab922e59da3d17832270fc6f943',
                       skey='45d38dc317e7b55bb7847ab54bf96011')


    # OK
    rsp =bione.query_balance()
    pprint(json.dumps(rsp))

    # j = {"symbol":"BTCUSDT","price":"9300","volume":"1","side":"BUY","type":"LIMIT"}
    # rsp = bione.commit_order(symbol='BTCUSDT', side='BUY', price=10000, volume=1)
    # print(rsp)


    # kline = bione.get_kline(symbol='BTCUSDT', interval='1day')
    # pprint(kline)


    orders = bione.get_cur_orders(symbol='HTDFUSDT' )
    print(orders['list'])
    print(len(orders['list']))
    #
    # ticker = bione.get_ticker(symbol='BTCUSDT')
    # pprint(ticker)

    # order = bione.query_order(symbol='BTCUSDT', id='150695552109032492')
    # print(order)

    # OK
    # rsp = bione.cancel_order(symbol='BTCUSDT', id='150695552109032492')
    # print(rsp)

    # rsp = bione.batch_order_cancel(symbol='BTCUSDT', ids=['150695552109032492'])
    # print(rsp)


    # print(rsp)
    # print(bione.ping())
    # print(bione.depth(symbol='BTCUSDT'))


    # #hc = TCClient(uid = '',akey=' 9e7fab136dd4694b531efdfddff5b48a',skey='625c9668ee53fbabe38e21786661fb9c')
    # #ticker = hc.Get_ticker('btcusdt')
    #
    # ret = hc.query_balance()
    # pprint(ret)
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


