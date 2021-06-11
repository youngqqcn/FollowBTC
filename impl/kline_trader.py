#!coding:utf8

#author:yqq
#date:2020/9/17 0017 18:37
#description: K线


import random
import numpy as np 
import time
import copy
from .header_ex_api import OKEX, HuoBi
from utils import round_down_float_all
from .order_booker import OrderBooker, TradeSide



class TakingSide:
    """K线的颜色"""
    UP = 'UP'  # 向上吃
    DOWN = 'DOWN'  # 向下吃



class KlineTrader(OrderBooker):

    def __init__(self, config_path: str, symbol: str):
        OrderBooker.__init__(self, config_path, symbol)

        conf = self.conf
        self.FlwVolMul  = conf[symbol]['FlwVolMul']
        self.order_amount_min = conf[symbol]['klinetrend']['order_amount_min']
        self.order_amount_max = conf[symbol]['klinetrend']['order_amount_max']
        self.kline_delay = conf[symbol]['klinetrend']['delay']
        self.amountmul = conf[symbol]['klinetrend']['amountmul']
        self.rt = conf[symbol]['klinetrend']['rt']
        self.order_num_min = conf[symbol]['klinetrend']['order_num_min']
        self.order_num_max = conf[symbol]['klinetrend']['order_num_max']
        pass

        # 得到目标价

    def get_baseprice_volume(self):
        try:
            # 目标涨跌幅
            if self.FlwExchange == 'Okex':
                fkline = self.okex.GetRate(self.Flwsymbol, self.period)
                T_rate = fkline['OK_rate']
                volume = fkline['OK_volume']
                if T_rate <= -1:
                    # Logging.info(tradesymbol+' 得到目标价错误')
                    raise Exception(self.tradesymbol + ' 得到目标价错误')
                ticker = self.tc.get_ticker(symbol=self.tradesymbol)
                nowprice = ticker['last']
                return (float(nowprice) * (1 + self.FlwMul * T_rate)), volume
            elif self.FlwExchange == 'HuoBi':
                fkline = self.hb.GetRate(self.Flwsymbol, self.period)
                T_rate = fkline['HB_rate']
                volume = fkline['HB_volume']
                if T_rate <= -1:
                    # Logging.info(tradesymbol+' 得到目标价错误')
                    raise Exception(self.tradesymbol + ' 得到目标价错误')

                # 昨天的收盘价作为今天基准价
                open_price = self.tc.get_base_price(symbol=self.tradesymbol, period=self.period)
                return (float(open_price) * (1 + self.FlwMul * T_rate)) , volume
            else:
                raise Exception("未知交易所 FlwExchange : {0}".format(self.FlwExchange))

        except Exception as e:
            # Logging.info(tradesymbol+' 得到目标价错误:{}'.format(e))
            print('得到目标价错误: {}'.format(e))
            raise e

    def make_orders(self):

        tarprice, tar_volume = self.get_baseprice_volume()
        print('目标价: {} , 目标成交量: {}'.format(tarprice, tar_volume))
        target_price = tarprice
        volume_next = self.FlwVolMul * tar_volume
        if volume_next < 10.:
            volume_next = 10.

        #获取最新成交价
        current_price = self.tc.get_latest_price(self.tradesymbol)

        # Logging.info(tradesymbol+' current_price:{}'.format(current_price))
        print(self.tradesymbol + ' current_price:{}'.format(current_price))

        if current_price == None or current_price < 0.00001:
            current_price = target_price
        if target_price == -1 :
            raise Exception("{} 获取目标价格错误".format(self.tradesymbol))
        if current_price == -1:
            raise Exception("{} 获取当前价格错误".format(self.tradesymbol))

        # Logging.info(tradesymbol+' target_price:{}, current_price:{}'.format(target_price, current_price))
        print(self.tradesymbol + ' target_price:{}, current_price:{}'.format(target_price, current_price))
        if target_price >= current_price:
            # Logging.info(tradesymbol+' 目标价大于或等于基本价')
            # 得到下单笔数 num + 1（targetprice）
            num = random.randint(self.order_num_min - 1, self.order_num_max - 1)
            # 得到下单价列表
            pricelist = np.random.uniform(target_price * 0.999, target_price, num)
            pricelist1 = list(pricelist) + [target_price]
            pricelist1 = sorted(round_down_float_all(pricelist1, self.PricePrecision))

            # 得到下单数量列表
            amountlist = np.random.uniform(volume_next * 0.8, volume_next * 1.2, num + 1)
            # Logging.info(tradesymbol+' 原始数量{}'.format(amountlist))
            amountlist_L = copy.deepcopy(amountlist)

            ratediff = (target_price - current_price) / current_price * 100
            if abs(ratediff) >= self.rt:
                # 跟随盘振幅偏大，数量倍系数，加大反手挂单量 by aether 2020年4月4日19:45:44
                amountlist_L = amountlist_L * (1 + abs(ratediff)) * self.amountmul
                # Logging.info(1+ abs(ratediff))
                # Logging.info(tradesymbol+" 反手单数量{}".format(amountlist_L))
            amountlist = round_down_float_all(list(amountlist), self.amount_precision)
            amountlist_L = round_down_float_all(list(amountlist_L), self.amount_precision)
            R = list(zip(pricelist1, amountlist))
            L = list(zip(pricelist1, amountlist_L))
            return TakingSide.UP, R, L[::-1]
        else:
            # Logging.info(tradesymbol+' 目标价小于基本价')
            # 得到下单笔数 num+1
            num = random.randint(self.order_num_min - 1, self.order_num_max - 1)
            # 得到下单价格列表
            pricelist = np.random.uniform(target_price, target_price * 1.001, num)
            pricelist1 = list(pricelist) + [target_price]
            pricelist1 = sorted(round_down_float_all(pricelist1, self.PricePrecision), reverse=True)

            # 得到下单数量列表
            amountlist = np.random.uniform(volume_next * 0.8, volume_next * 1.2, num + 1)
            # Logging.info(tradesymbol+" 原始数量{}".format(amountlist))
            amountlist_L = copy.deepcopy(amountlist)

            ratediff = (target_price - current_price) / current_price * 100
            if abs(ratediff) >= self.rt:
                amountlist_L = amountlist_L * (1 + abs(ratediff) * self.amountmul)
                # Logging.info(1 + abs(ratediff)*amountmul)
                # Logging.info(tradesymbol+" 反手单数量{}".format(amountlist_L))
            amountlist = round_down_float_all(list(amountlist), self.amount_precision)
            amountlist_L = round_down_float_all(list(amountlist_L), self.amount_precision)
            R = list(zip(pricelist1, amountlist))
            L = list(zip(pricelist1, amountlist_L))
            return TakingSide.DOWN, R, L[::-1]


        pass


    def trade_loop(self, per_loop_interval_secs: float = 5.0):
        #阻塞

        while True:
            try:
                side, R, L = self.make_orders()
                if side == TakingSide.UP and R != [] and L != []:
                    # 向上吃单

                    # 铺卖单
                    ret = self.submit_orders(side=TradeSide.SELL, orders=R, dealy=1.5)
                    time.sleep(0.5)
                    # 下反手买单
                    ret = self.submit_orders(side=TradeSide.BUY, orders=L, dealy=self.kline_delay)
                    # 反手单加量的时候，撤单
                    if L[-1][1] / R[0][1] > 1.001:
                        time.sleep(1)
                        self.tc.cancel_orders(self.tradesymbol, ret)
                elif side == TakingSide.DOWN and R != [] and L != []:
                    # 向下吃单

                    # 铺买单
                    ret = self.submit_orders(side=TradeSide.BUY, orders=R, dealy=1.5)
                    time.sleep(0.5)

                    # 下反手卖单
                    ret = self.submit_orders(side=TradeSide.SELL, orders=L, dealy=self.kline_delay)

                    if L[-1][1] / R[0][1] > 1.001:
                        time.sleep(1)
                        self.tc.cancel_orders(self.tradesymbol, ret)
                else:
                    raise Exception("invalid side {}".format(side))
            except Exception as e:
                print('trade_loop error: {}'.format(e))

            time.sleep(per_loop_interval_secs)

        pass


    def startloop(self):
        self.trade_loop(per_loop_interval_secs=1.0)  #阻塞
        pass


#
#
# if __name__ == '__main__':
#
#     kt = KlineTrader(config_path='../config.yml', symbol='HTDF/USDT')
#     kt.startloop()
#
#     pass