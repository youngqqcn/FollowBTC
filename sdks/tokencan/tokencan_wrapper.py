#!coding:utf8

#author:yqq
#date:2020/9/17 0017 18:37
#description:

import os
import sys
import random
import time
import datetime
from os.path import dirname
from  .tokencan_proxy import TokenCanProxy
sys.path.insert(0, dirname(os.path.abspath(__file__)))


class TokenCanWrapper(object):
    def __init__(self, akey: str, skey: str):
        super(TokenCanWrapper, self).__init__()
        self.tc = TokenCanProxy(uid='', akey=akey, skey=skey)
    
    #限价买单
    def buy_in_limit_price(self, symbol, price, amount):
        ret = self.tc.order_commit(symbol,'BUY',price,amount)
        return ret['data']['order_id']

    def sell_in_limit_price(self, symbol, price, amount):
        ret = self.tc.order_commit(symbol, 'SELL', price, amount)
        return ret['data']['order_id']


    def get_base_price(self, symbol, period: str):
        """
        获取基准价
        :param symbol:
        :param period:
        :return:
        """
        if period in ['1day', 'day']:
            period =  24 * 60
        elif 'm' in period:
            minutes = int(period[0: period.find('m')])
            period = minutes
        elif 'h' in period:
            hours = int(period[0: period.find('h')])
            period = hours * 60
        else:
            raise Exception("unknown period {}".format(period))


        time_today_00_00_00 = int(time.mktime(datetime.date.today().timetuple()))
        time_yesterday_23_59_00 = time_today_00_00_00 - 60
        secs = int(time.time()) - time_today_00_00_00
        sleep_secs = 10
        if period == 24 * 60 and 0 < secs < 60 and  sleep_secs >= secs:
            time.sleep((sleep_secs - int(secs)) % (sleep_secs + 1))

        kline = self.tc.get_records(symbol=symbol, period=period)
        kline = kline['data']
        assert isinstance(kline, list), 'kline is not list'
        assert len(kline[-1]) >= 4, 'kline data is invalid'
        kl_timestamp = kline[-1][0]

        # 到了晚上十二点整的时候, 因T网的日成交数据生成有延时, 导致获取的是前天的收盘价!  而火币又更新了当前的涨跌幅
        if period == 24 * 60 and  kl_timestamp != time_today_00_00_00 - (24 * 60 * 60):
            if 0 < secs < 60:  # 00:00:00 至  00:00:59
                if sleep_secs >= secs:
                    time.sleep((sleep_secs - int(secs)) % (sleep_secs + 1))  # 第一次休眠
                for n in range(6):
                    kline = self.tc.get_records(symbol=symbol, period=1)  # 获取1分钟k线
                    kline = kline['data']
                    latest_10_kl = kline[-10:]  # 最后10根分钟线
                    for kl in latest_10_kl[::-1]:
                        if kl[0] == time_yesterday_23_59_00:
                            return kl[4]  # 前一天的 23:59 的收盘价作为今天的基准价
                    time.sleep(sleep_secs)

            print('GetBasePrice: invalid kline  kl_timestamp ')
            raise Exception("GetBasePrice: invalid kline  kl_timestamp ")

        return kline[-1][4]

    def get_ticker(self, symbol):
        ticker = self.tc.get_ticker(symbol)
        return {"buy":0, "sell":0, "last":ticker}


    def get_latest_price(self, symbol):
        ticker = self.tc.get_ticker(symbol)
        return ticker

        
    def get_order_info(self, symbol, id):
        o_info = self.tc.query_order(symbol, id)
        return o_info

    def get_orders(self, symbol, page_size=100):
        os = self.tc.query_entrust_cur(symbol, count=page_size)
        return os['data']['resultList']


    def cancel_order(self, symbol, id):
        ret = self.tc.order_cancel(symbol,id)
        return ret

    def cancel_orders(self, symbol, ordids, delay = 0):
        for id in ordids:
            self.tc.order_cancel(symbol, id)
            time.sleep(delay)

    def cancel_all_orders(self, symbol):
        ret = self.tc.batch_order_cancel(symbol)
        return ret


    def get_account_balance(self, symbols: list):
        """
        :param symbols:
        :return: {'htdf': {"coin":"htdf","normal":32323.233,"locked":32323.233,"btcValuatin":112.33} , ....}
        """
        ret = self.tc.query_balance()
        symbol_list = [ str(symb.lower()) for symb in symbols ]
        rets = {}
        for coin in ret:
            if coin['coin'] in symbol_list:
                rets[coin['coin']] = coin
        return rets

    #撤掉超时未成交订单
    def cancel_timeout_orders(self, symbol, max_lifetime, min_ords_count=0, delay=0.001):
        now_time = int(time.time())
        orders = self.get_orders(symbol)
        random.shuffle(orders)
        if len(orders) <= min_ords_count:
            return

        for order in orders:
            order_time = int(order['created_at'] / 1000)
            if now_time - order_time < max_lifetime:
                continue
            self.cancel_order(symbol, order['id'])
            time.sleep(delay)



        



