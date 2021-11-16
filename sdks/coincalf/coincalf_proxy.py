#!coding:utf8

# author:yqq
# date:2020/9/17 0017 18:37
# description:

import json
import requests
import sys
import os
from os.path import dirname
from datetime import datetime

sys.path.insert(0, dirname(os.path.abspath(__file__)))


class CoincalfProxy:
    API_HOST = 'https://www.bileex.com'

    URI_ORDER_COMMIT = '/v1/order/place'
    URI_ORDER_CANCEL = '/v1/order/cancel'
    URI_ORDER_CANCEL_ALL = '/v1/order/batchCancelOrders'
    URI_ORDER_INFO = '/v1/order/entrust'
    URI_BALANCE = '/v1/balance'

    # 测试成功
    URI_ORDER_ENTRUST = '/v2/s/trade/order/entrusts'
    URI_ORDER_ENTRUST_CANCEL = '/v2/s/trade/order/entrusts/{}'
    URI_QUERY_CURRENT_ORDERS = "/v2/s/trade/order/entrusts/{}/{}/{}"
    URI_TICKER = '/v2/s/trade/market/ticker/{}'
    URI_KLINE = '/v2/s/trade/market/kline/{}/{}/{}'

    def __init__(self, **kwargs):
        self.uid = kwargs.get('uid')
        self.TOKEN = kwargs.get('token')
        # self.akey = kwargs.get('akey')
        # self.skey = kwargs.get('skey')

    @staticmethod
    def http_post_request(url, params=None, header=None, timeout=10):
        response = requests.post(url, params, timeout=timeout, headers=header)
        if response.status_code != 200:
            raise Exception('http error code:{}'.format(response.status_code))
        json_rsp = response.json()
        return json_rsp

    @staticmethod
    def direct_http_get(url, params=None, header=None, timeout=10):
        response = requests.get(url, params=params, headers=header, timeout=timeout)
        print(response)
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

    # def params_sign(self, params, paramsPrefix, accessSecret):
    #
    #     host = "hkapi.hotcoin.top"
    #     method = paramsPrefix['method'].upper()
    #     uri = paramsPrefix['uri']
    #     tempParams = urllib.parse.urlencode(sorted(params.items(), key=lambda d: d[0], reverse=False))
    #     payload = '\n'.join([method, host, uri, tempParams]).encode(encoding='UTF-8')
    #
    #     # print("payload: {}".format(payload))
    #
    #     accessSecret = accessSecret.encode(encoding='UTF-8')
    #     return base64.b64encode(hmac.new(accessSecret, payload, digestmod=hashlib.sha256).digest())

    @staticmethod
    def get_utc_str():
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # def _api_key_post(self, params, api_uri, timeout=10):
    #     method = 'POST'
    #     params_to_sign = {'AccessKeyId': self.akey,
    #                       'SignatureMethod': 'HmacSHA256',
    #                       'SignatureVersion': '2',
    #                       'Timestamp': self.get_utc_str()}
    #     url = CoincalfProxy.API_RUL + api_uri
    #     host_name = urllib.parse.urlparse(url).hostname
    #     host_name = host_name.lower()
    #     params_prefix = {"host": host_name, 'method': method, 'uri': api_uri}
    #     params_to_sign.update(params)
    #     params_to_sign['Signature'] = self.params_sign(params_to_sign, params_prefix, self.skey).decode(
    #         encoding='UTF-8')
    #
    #     return self.http_post_request(url, params_to_sign, timeout)
    #
    # def _api_key_get(self, params, api_uri, timeout=10):
    #     method = 'GET'
    #     params_to_sign = {'AccessKeyId': self.akey,
    #                       'SignatureMethod': 'HmacSHA256',
    #                       'SignatureVersion': '2',
    #                       'Timestamp': self.get_utc_str()}
    #
    #     url = CoincalfProxy.API_RUL + api_uri
    #
    #     host_name = urllib.parse.urlparse(url).hostname
    #     host_name = host_name.lower()
    #     params_prefix = {"host": host_name, 'method': method, 'uri': api_uri}
    #     params_to_sign.update(params)
    #
    #     params_to_sign['Signature'] = self.params_sign(params_to_sign, params_prefix, self.skey).decode(
    #         encoding='UTF-8')
    #     # print("sig:{}".format( params_to_sign['Signature'] ))
    #
    #     return self.direct_http_get(url=url, params=params_to_sign, timeout=timeout)

    def get_ticker(self, symbol, timeout=10):
        """ticker"""

        uri = CoincalfProxy.URI_TICKER.format(symbol)
        url = self.API_HOST + uri

        rsp = self.direct_http_get(url=url, header={'token': self.TOKEN}, timeout=timeout)
        data = rsp['data']
        if isinstance(data, str):
            # ticker接口返回的data有问题，特殊处理
            tmp = json.loads(data)
            if isinstance(tmp, str):
                return json.loads(tmp)
        return data

    def get_records(self, symbol, kline_type, size, timeout=10):
        """
        获取K线数据
        kline_type:  1min , 5min, 15min, 30min, 60min, 4hour, 1day, 1week, 1mon, 1year,
        """
        url = self.API_HOST + self.URI_KLINE.format(symbol, kline_type, size)
        rsp = self.direct_http_get(url=url, header={'token': self.TOKEN}, timeout=timeout)
        return rsp

    # def query_balance(self, timeout=10):
    #     uri = CoincalfProxy.URI_BALANCE
    #     p = {}
    #     rsp = self._api_key_get(p, uri, timeout)
    #     # print(ret)
    #     acc = rsp['data']['wallet']
    #     return acc

    # def query_order(self, symbol, id, timeout=10):
    #     p = {'symbol': symbol, 'order_id': id}
    #     ret = self._api_key_get(p, CoincalfProxy.URI_ORDER_INFO, timeout)
    #     return ret

    def query_current_orders(self, symbol: str, cur_page: int, page_size: int = 100, timeout=10):
        """
        查询当前委托订单
        {'total': 1, 'size': 100, 'pages': 1, 'current': 0, 'records': [{'orderId': '1460547581960089601', 'type': 2, 'price': 5.12, 'dealAvgPrice': 0, 'volume': 20.0, 'dealVolume': 0.0, 'amount': 102.4, 'dealAmount': 0, 'status': 0, 'created': '2021-11-16 17:57:33', 'symbol': 'NFCUSDT'}]}
        """
        url = self.API_HOST + self.URI_QUERY_CURRENT_ORDERS.format(symbol, cur_page, page_size)
        rsp = self.direct_http_get(url=url, header={'token': self.TOKEN}, timeout=timeout)
        if rsp['errcode'] != 0: return rsp['errmsg']
        return rsp['data']

    def order_commit(self, symbol, order_type, price, amount, price_type, timeout=10):
        url = self.API_HOST + self.URI_ORDER_ENTRUST
        p = {'type': order_type, 'volume': amount, 'price': price, 'symbol': symbol, 'priceType': price_type}
        header = {
            'token': self.TOKEN,
            'Content-Type': 'application/json'
        }
        rsp = self.http_post_request(url=url,  params=json.dumps(p), header=header, timeout=timeout)
        if rsp['errcode'] != 0: return rsp['errmsg']
        return rsp['data']

    def order_cancel(self, oid: str, timeout=10):
        url = self.API_HOST + self.URI_ORDER_ENTRUST_CANCEL.format(oid)
        response = requests.delete(url,  timeout=timeout, headers={'token': self.TOKEN})
        if response.status_code != 200:
            raise Exception('http error code:{}'.format(response.status_code))
        json_rsp = response.json()
        return json_rsp

    def batch_cancel_orders(self, symbol: str):
        """批量撤单"""
        cur_page = 0
        page_size = 100
        order_ids = []
        pages = 1
        while cur_page < pages:
            rsp = self.query_current_orders(symbol=symbol, cur_page=cur_page, page_size=page_size)
            cur_page += 1
            pages = rsp['pages']
            records = rsp['records']
            for r in records:
                order_ids.append(r['orderId'])
            pass

        for oid in order_ids:
            self.order_cancel(oid=oid)
        return


if __name__ == '__main__':
    hc = CoincalfProxy(uid='',
                       token='eyJ1c2VybmFtZSI6ImFhYWFxcXFxQDEyNi5jb20ifQ==.0eac84d540ad6648e852e18e3b6d3488',
                       akey='c1c3d0cbadc94574b499f673d5baceeb',
                       skey='37D4A610C69E3689FFD149A46FA16990')

    # 测试获取当前成交价
    # ticker = hc.get_ticker(symbol='NFCUSDT')
    # print(ticker)

    # 测试下单
    # ret = hc.order_commit(symbol='NFCUSDT', price=5.12, amount=20, order_type=2, price_type=1)
    # print(ret)
    # {'errcode': 0, 'errmsg': 'ok', 'data': {'errcode': 0, 'errmsg': 'ok', 'data': {'id': '1460536933679198209', 'userId': '1459421942771195905', 'marketId': '3', 'marketType': 1, 'symbol': 'NFCUSDT', 'marketName': 'NFC/USDT', 'price': 5.12, 'mergeLowPrice': 5.12, 'mergeHighPrice': 5.12, 'volume': 20, 'amount': 102.4, 'feeRate': 0.002, 'fee': 0.2048, 'deal': 0, 'freeze': 20, 'priceType': 1, 'tradeType': 1, 'type': 2, 'status': 0, 'lastUpdateTime': '2021-11-16 17:15:15', 'created': '2021-11-16 17:15:15'}}}

    # 测试撤单
    # ret = hc.order_cancel(oid='1460536933679198209')
    # print(ret)

    # 查询当前的订单
    # ret = hc.query_current_orders(symbol='NFCUSDT', cur_page=0)
    # print(ret)

    # 查询某笔订单
    # ret = hc.query_order()

    ret = hc.get_records(symbol='NFCUSDT', kline_type='1day', size=100)
    print(ret)


    pass


