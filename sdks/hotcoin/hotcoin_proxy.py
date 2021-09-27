#!coding:utf8

# author:yqq
# date:2020/9/17 0017 18:37
# description:

import hashlib
import time
import requests
import sys
import os
from pprint import pprint
from os.path import dirname
import urllib
from datetime import datetime
import base64
import hmac
sys.path.insert(0, dirname(os.path.abspath(__file__)))


class HotcoinProxy:
    # API_RUL = 'https://openapi.tokencan.net'
    API_RUL = 'https://hkapi.hotcoin.top'

    URI_ORDER_COMMIT = '/v1/order/place'
    URI_ORDER_CANCEL = '/v1/order/cancel'
    URI_ORDER_CANCEL_ALL = '/v1/order/batchCancelOrders'
    URI_ORDER_ENTRUST = '/v1/order/entrust'
    URI_ORDER_INFO = '/v1/order/entrust'

    URI_BALANCE = '/v1/balance'
    URI_TICKER = '/v1/ticker'
    #URI_GETRECORDS = '/open/api/get_records'

    def __init__(self, **kwargs):
        self.uid = kwargs.get('uid')
        self.akey =  kwargs.get('akey')
        self.skey = kwargs.get('skey')

    @staticmethod
    def http_post_request(url, params=None, timeout=10):
        response = requests.post(url, params, timeout=timeout)
        if response.status_code != 200:
            raise Exception('http error code:{}'.format(response.status_code))
        json_rsp = response.json()
        return json_rsp

    @staticmethod
    def direct_http_get(url, params=None, timeout=10):
        response = requests.get(url, params=params, timeout=timeout)
        print(response)
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



    def params_sign(self, params, paramsPrefix, accessSecret):

        host = "hkapi.hotcoin.top"
        method = paramsPrefix['method'].upper()
        uri = paramsPrefix['uri']
        tempParams = urllib.parse.urlencode(sorted(params.items(), key=lambda d: d[0], reverse=False))
        payload = '\n'.join([method, host, uri, tempParams]).encode(encoding='UTF-8')

        # print("payload: {}".format(payload))

        accessSecret = accessSecret.encode(encoding='UTF-8')
        return base64.b64encode(hmac.new(accessSecret, payload, digestmod=hashlib.sha256).digest())



    def http_post_request(self, url, params, timeout=10):
        response = requests.post(url, params, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            return

    def get_utc_str(self):
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _api_key_post(self, params, api_uri, timeout=10):
        method = 'POST'
        params_to_sign = {'AccessKeyId': self.akey,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': self.get_utc_str()}
        url = HotcoinProxy.API_RUL + api_uri
        host_name = urllib.parse.urlparse(url).hostname
        host_name = host_name.lower()
        params_prefix = {"host": host_name, 'method': method, 'uri': api_uri}
        params_to_sign.update(params)
        params_to_sign['Signature'] = self.params_sign(params_to_sign, params_prefix, self.skey).decode(encoding='UTF-8')

        return self.http_post_request(url, params_to_sign, timeout)

    def _api_key_get(self, params, api_uri, timeout=10):
        method = 'GET'
        params_to_sign = {'AccessKeyId': self.akey,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': self.get_utc_str()}

        url = HotcoinProxy.API_RUL + api_uri

        host_name = urllib.parse.urlparse(url).hostname
        host_name = host_name.lower()
        paramsPrefix = {"host": host_name, 'method': method, 'uri': api_uri}
        params_to_sign.update(params)

        params_to_sign['Signature'] = self.params_sign(params_to_sign, paramsPrefix, self.skey).decode(encoding='UTF-8')
        # print("sig:{}".format( params_to_sign['Signature'] ))

        return self.direct_http_get(url=url,  params=params_to_sign,   timeout=timeout)


    def get_ticker(self, symbol, step, timeout=10):
        uri = HotcoinProxy.URI_TICKER

        p = {"symbol": symbol, "step": step}
        ret = self._api_key_get(params=p, api_uri=uri, timeout=timeout)

        # ticker = ret['data'][symbol]

        return ret

    #(get请求)获取K线数据
    def get_records(self, symbol, period, timeout=10):
        # p = {'symbol': symbol, 'period': period}
        # ret = self._api_key_get(p, HotcoinProxy.URI_GETRECORDS, timeout)

        return self.get_ticker(symbol=symbol, step=period)


    def query_balance(self, timeout=10):
        uri =   HotcoinProxy.URI_BALANCE
        p = {}
        ret = self._api_key_get(p, uri, timeout)
        # print(ret)
        acc = ret['data']['wallet']
        return acc


    def query_order(self, symbol, id, timeout=10):
        p = {'symbol': symbol, 'order_id': id}
        ret = self._api_key_get(p, HotcoinProxy.URI_ORDER_INFO, timeout)
        return ret

    def query_entrust_cur(self, symbol: str, count: int = 100, timeout=10):
        p = {'symbol': symbol, 'count': count, 'type': 1}

        ret = self._api_key_get(p, HotcoinProxy.URI_ORDER_ENTRUST, timeout)
        # print(ret)
        return ret

    def order_commit(self, symbol, type, price, amount, timeout=10):
        p = {'type': type, 'tradeAmount': amount, 'tradePrice': price, 'symbol': symbol}
        ret = self._api_key_post(p, HotcoinProxy.URI_ORDER_COMMIT, timeout)

        return ret

    def order_cancel(self, symbol, id, timeout=10):
        p = {'symbol': symbol, 'id': id}
        ret = self._api_key_post(p, HotcoinProxy.URI_ORDER_CANCEL, timeout)
        return ret

    def batchCancelOrders(self, symbol, timeout=10):
        p = {'symbol': symbol}
        ret = self._api_key_post(p, HotcoinProxy.URI_ORDER_CANCEL_ALL, timeout)
        return ret


if __name__ == '__main__':
    hc = HotcoinProxy(uid='',
                       akey='c1c3d0cbadc94574b499f673d5baceeb',
                       skey='37D4A610C69E3689FFD149A46FA16990')
    # hc = TCClient(uid = '',akey=' 9e7fab136dd4694b531efdfddff5b48a',skey='625c9668ee53fbabe38e21786661fb9c')
    # ticker = hc.Get_ticker('btcusdt')



    # test ok
    # ret = hc.order_commit(symbol='htdf_usdt', type='sell', price=0.06, amount=1)
    # pprint(ret)


    # test ok
    # ret = hc.query_balance()
    # pprint(ret)


    # ret = hc.get_ticker(symbol='htdf_usdt', step=86400)
    # print(ret)
    # test ok
    # ret = hc.get_records(symbol='htdf_usdt', period=86400)
    # pprint(ret)


    #
    # print(ret,len(ret))
    #
    # id = hc.order_commit(symbol='htdf_usdt', type='sell', price=0.06, amount=2, timeout= 10)
    #
    # print(id)


    # test ok
    # id = '32401090'
    # oi = hc.query_order('htdf_usdt', id)
    # pprint(oi)

    # os = hc.query_entrust_cur(symbol='htdf_usdt', count=100, timeout=10)
    # pprint(os)

    # ret = hc.order_cancel(symbol='htdf_usdt',id='7066868693')
    # print(ret)
    # ret = hc.batchCancelOrders('htdf_usdt',id='7067730548')
    # print(ret)

    # klines = hc.get_records(symbol='htdfusdt', period=1440, timeout=10)
    # pprint(klines)


