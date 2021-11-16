#!coding:utf8

# author:yqq
# date:2020/9/17 0017 18:37
# description:

import os
import sys
import random
import time
import datetime
from os.path import dirname
from pprint import pprint
from coincalf_proxy import CoincalfProxy

sys.path.insert(0, dirname(os.path.abspath(__file__)))


class CoincalfWrapper(object):

    ORDER_TYPE_BUY = 1
    ORDER_TYPE_SELL = 2

    PRICE_TYPE_LIMIT = 1  # 限价
    PRICE_TYPE_MARKET = 2  # 市价

    def __init__(self, token: str = '', akey: str = '', skey: str = ''):
        super(CoincalfWrapper, self).__init__()
        self.proxy = CoincalfProxy(uid='', token=token, akey=akey, skey=skey)

    def buy_in_limit_price(self, symbol, price, amount):
        """限价买"""

        ret = self.proxy.order_commit(symbol=symbol, order_type=self.ORDER_TYPE_BUY,
                                      price=price, amount=amount, price_type=self.PRICE_TYPE_LIMIT)
        print(ret)
        if not isinstance(ret, dict):
            raise Exception("invalid ret {}".format(ret))
        if ret['errcode'] != 0:
            raise Exception('{}'.format(ret['errmsg']))
        return ret['data']['id']

    def sell_in_limit_price(self, symbol, price, amount):
        """限价卖"""

        ret = self.proxy.order_commit(symbol=symbol, order_type=self.ORDER_TYPE_SELL,
                                      price=price, amount=amount, price_type=self.PRICE_TYPE_LIMIT)
        print(ret)
        if not isinstance(ret, dict):
            raise Exception("invalid ret {}".format(ret))
        if ret['errcode'] != 0:
            raise Exception('{}'.format(ret['errmsg']))
        return ret['data']['id']

    def get_base_price(self, symbol, kline_type: str):
        """
        获取基准价, 获取昨天的收盘价，作为今天基准价
        """
        assert kline_type in ['1min', '5min', '15min', '30min', '60min',
                                      '4hour', '1day', '1week', '1mon', '1year'], 'invalid peri'

        time_today_00_00_00 = int(time.mktime(datetime.date.today().timetuple()))
        time_yesterday_23_59_00 = time_today_00_00_00 - 60
        secs = int(time.time()) - time_today_00_00_00
        sleep_secs = 10
        if kline_type == 24 * 60 and 0 < secs < 60 and sleep_secs >= secs:
            time.sleep((sleep_secs - int(secs)) % (sleep_secs + 1))

        # 获取日k线
        kline = self.proxy.get_records(symbol=symbol, kline_type=kline_type, size=2)
        kline = kline['data']
        assert isinstance(kline, list), 'kline is not list'
        assert len(kline) >= 0, 'kline data is invalid'

        # TODO: 如果coincalf也存在同样问题，需要放开以下代码。暂时不放开
        # kl_timestamp = int(int(kline[0]['id']) / 1000)
        # # 到了晚上十二点整的时候, 因T网的日成交数据生成有延时, 导致获取的是前天的收盘价!  而火币又更新了当前的涨跌幅
        # if kline_type == '1day' and kl_timestamp != time_today_00_00_00 - (24 * 60 * 60):
        #     if 0 < secs < 60:  # 00:00:00 至  00:00:59
        #         if sleep_secs >= secs:
        #             time.sleep((sleep_secs - int(secs)) % (sleep_secs + 1))  # 第一次休眠
        #         for n in range(6):
        #             kline = self.proxy.get_records(symbol=symbol, kline_type='1min', size=10)  # 获取1分钟k线
        #             kline = kline['data']
        #             latest_10_kl = kline[-10:]  # 最后10根分钟线
        #             for kl in latest_10_kl[::-1]:
        #                 if kl[0] == time_yesterday_23_59_00:
        #                     return kl[4]  # 前一天的 23:59 的收盘价作为今天的基准价
        #             time.sleep(sleep_secs)
        #
        #     print('GetBasePrice: invalid kline  kl_timestamp ')
        #     raise Exception("GetBasePrice: invalid kline  kl_timestamp ")

        return kline[1]['close']  # 收盘价

    # 获取盘口买一,卖一
    def get_ticker(self, symbol):
        """ticker"""
        ticker = self.proxy.get_ticker(symbol)
        return {"buy": 0, "sell": 0, "last": ticker}

    def get_latest_price(self, symbol):
        """获取最新成交价"""
        ticker = self.proxy.get_ticker(symbol)
        return ticker['close']

    # def get_order_info(self, symbol, oid):
    #     o_info = self.proxy.
    #     return o_info

    def get_orders(self, symbol, page_size=100):
        """获取委托单"""
        data = self.proxy.query_current_orders(symbol, cur_page=0, page_size=page_size)
        return data['records']

    def get_all_cur_orders(self, symbol):
        """获取此币对所有委托订单"""
        data = self.proxy.query_current_orders(symbol, cur_page=0, page_size=100)
        orders = data['records']
        for cp in range(1, int(data['pages'])):
            d = self.proxy.query_current_orders(symbol, cur_page=cp, page_size=100)
            orders.extend(d['records'])
        return orders

    def cancel_order(self, oid):
        """撤单"""
        ret = self.proxy.order_cancel(oid)
        return ret

    def cancel_orders(self,  order_ids, delay=0):
        """批量撤单"""
        for oid in order_ids:
            self.proxy.order_cancel( oid)
            time.sleep(delay)

    def cancel_all_orders(self, symbol):
        """撤销当前币对所有委托订单"""
        ret = self.proxy.batch_cancel_orders(symbol=symbol)
        return ret

    # TODO: 获取账户余额
    # def get_account_balance(self, symbols: list):
    #     """
    #     :param symbols:
    #     :return: {'htdf': {"coin":"htdf","normal":32323.233,"locked":32323.233,"btcValuatin":112.33} , ....}
    #     """
    #     ret = self.proxy.query_balance()
    #     symbol_list = [str(symb.lower()) for symb in symbols]
    #     rets = {}
    #     for coin in ret:
    #         if coin['coin'] in symbol_list:
    #             rets[coin['coin']] = coin
    #     return rets

    def cancel_timeout_orders(self, symbol, max_lifetime, min_ords_count=0, delay=0.001):
        """撤掉超时未成交订单"""

        now_time = int(time.time())
        orders = self.get_orders(symbol)
        random.shuffle(orders)
        if len(orders) <= min_ords_count:
            return

        for order in orders:
            tm = order['created']
            order_time = int(time.mktime(time.strptime(tm, "%Y-%m-%d %H:%M:%S")))
            if now_time - order_time < max_lifetime:
                continue
            self.cancel_order(order['orderId'])
            time.sleep(delay)


def main():
    hc = CoincalfWrapper(token='eyJ1c2VybmFtZSI6ImFhYWFxcXFxQDEyNi5jb20ifQ==.0eac84d540ad6648e852e18e3b6d3488',
                         akey='c1c3d0cbadc94574b499f673d5baceeb',
                         skey='37D4A610C69E3689FFD149A46FA16990')

    # ret = hc.buy_in_limit_price(symbol='NFCUSDT', price='6.8', amount='20')
    # pprint(ret)

    ret = hc.sell_in_limit_price(symbol='NFCUSDT', price='6.5', amount='30')
    pprint(ret)

    # ret = hc.get_base_price(symbol='NFCUSDT', kline_type='1day')
    # pprint(ret)

    ret = hc.get_latest_price(symbol='NFCUSDT')
    print(ret)

    pass


if __name__ == '__main__':
    main()









