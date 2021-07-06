#!coding:utf8

#author:yqq
#date:2021/06/15
#description:

import os
import sys
import random
import time
import datetime
from os.path import dirname
from  .bione_proxy import BioneProxy
sys.path.insert(0, dirname(os.path.abspath(__file__)))


class BioneWrapper(object):
    def __init__(self, akey: str, skey: str):
        super(BioneWrapper, self).__init__()
        self.proxy = BioneProxy(uid='', akey=akey, skey=skey)

    #限价买单
    def buy_in_limit_price(self, symbol, price, amount):
        ret = self.proxy.commit_order(symbol=symbol, side='BUY', price=price, volume=amount)
        return ret['orderId']

    def sell_in_limit_price(self, symbol, price, amount):
        ret = self.proxy.commit_order(symbol= symbol, side='SELL', price=price, volume=amount)
        return ret['orderId']


    def get_base_price(self, symbol, period: str):
        """
        获取基准价
        :param symbol:
        :param period:
        :return:

        ======response
        [
            {
                "high": "6228.77",
                "vol": "111",
                "low": "6228.77",
                "idx": 1594640340,
                "close": "6228.77",
                "open": "6228.77"
            },
            ....
        ]

        """
        # if period in ['1day', 'day']:
        #     period =  24 * 60
        # elif 'm' in period:
        #     minutes = int(period[0: period.find('m')])
        #     period = minutes
        # elif 'h' in period:
        #     hours = int(period[0: period.find('h')])
        #     period = hours * 60
        # else:
        #     raise Exception("unknown period {}".format(period))
        #
        #
        time_today_00_00_00 = int(time.mktime(datetime.date.today().timetuple()))
        now  = int(time.time())
        if (23*60*60 + 59*60 <=  (now - time_today_00_00_00) <= 24*60*60)\
                or ( 0 <= (now - time_today_00_00_00) <= 1*60 ):
            time.sleep(128)
            raise Exception("为了保证K线的正确, 23:59:00 ~ 00:01:00 之间不进行交易")

        kline = self.proxy.get_kline(symbol=symbol, interval=period)
        # kline = kline['data']
        # assert isinstance(kline, list), 'kline is not list'
        # assert len(kline[-1]) >= 4, 'kline data is invalid'
        # kl_timestamp = kline[-1][0]

        # 到了晚上十二点整的时候, 因T网的日成交数据生成有延时, 导致获取的是前天的收盘价!  而火币又更新了当前的涨跌幅
        # if period == 24 * 60 and  kl_timestamp != time_today_00_00_00 - (24 * 60 * 60):
        #     if 0 < secs < 60:  # 00:00:00 至  00:00:59
        #         if sleep_secs >= secs:
        #             time.sleep((sleep_secs - int(secs)) % (sleep_secs + 1))  # 第一次休眠
        #         for n in range(6):
        #             kline = self.tc.get_records(symbol=symbol, period=1)  # 获取1分钟k线
        #             kline = kline['data']
        #             latest_10_kl = kline[-10:]  # 最后10根分钟线
        #             for kl in latest_10_kl[::-1]:
        #                 if kl[0] == time_yesterday_23_59_00:
        #                     return kl[4]  # 前一天的 23:59 的收盘价作为今天的基准价
        #             time.sleep(sleep_secs)
        #
        #     print('GetBasePrice: invalid kline  kl_timestamp ')
        #     raise Exception("GetBasePrice: invalid kline  kl_timestamp ")
        # return kline[-1][4]

        # 获取上一个收盘价, 因为bione的response按照时间戳降序的, 所以取第一个即可
        return kline[0]['close']

    def get_ticker(self, symbol):
        """
        response 示例:
        {
            'buy': 40255.8674,
            'high': '40990.0833',
            'last': '40256.3751',
            'low': '38752.2702',
            'open': '40686.3521',
            'rose': '-0.0105680892',
            'sell': 40256.8826,
            'time': 1623724580000,
            'vol': '11761.07109632'
        }
        """
        ticker = self.proxy.get_ticker(symbol)
        return ticker


    def get_latest_price(self, symbol):
        """
        ticker 响应内容
        {
            "high": "9279.0301",
            "vol": "1302",
            "last": "9200",
            "low": "9279.0301",
            "rose": "0",
            "time": 1595563624731
        }

        """
        ticker = self.proxy.get_ticker(symbol)
        return float(ticker['last'])


    def get_order_info(self, symbol, id):
        o_info = self.proxy.query_order(symbol, id)
        return o_info

    def get_orders(self, symbol, page_size=100):
        orders = self.proxy.get_cur_orders(symbol, limit=page_size)
        return orders['list']


    def cancel_order(self, symbol, id):
        ret = self.proxy.cancel_order(symbol, id)
        return ret

    def cancel_orders(self, symbol, ordids, delay = 0):
        # 为了防止撤单太快, 不使用批量撤单接口, 而是采用单笔撤单
        # return self.proxy.batch_order_cancel(symbol, ordids)
        for id in ordids:
            self.cancel_order(symbol=symbol, id=id)
            time.sleep(delay)

    def cancel_all_orders(self, symbol):
        for i in range(3):
            orders = self.get_orders(symbol, page_size=500)
            order_ids = []
            for ord in orders:
                order_ids.append(ord['orderId'])
            ret = self.proxy.batch_order_cancel(symbol, order_ids)
            return ret


    def get_account_balance(self, symbols: list):
        """
        :param symbols:
        :return: {'htdf': {"coin":"htdf","normal":32323.233,"locked":32323.233,"btcValuatin":112.33} , ....}
        """
        ret = self.proxy.query_balance()
        symbol_list = [ str(symb.lower()) for symb in symbols ]
        rets = {}
        for coin in ret:
            symbol = str(coin['asset']).lower()
            if symbol in symbol_list:
                rets[symbol] = {'free': coin['free'], 'locked': coin['locked'] }
        return rets

    #撤掉超时未成交订单
    def cancel_timeout_orders(self, symbol, max_lifetime, min_ords_count=0, delay=0.001):
        now_time = int(time.time())
        orders = self.get_orders(symbol)
        random.shuffle(orders)
        if len(orders) <= min_ords_count:
            return

        for order in orders:
            order_time = int(order['time'] / 1000)
            if now_time - order_time < max_lifetime:
                continue
            self.cancel_order(symbol, order['id'])
            time.sleep(delay)







