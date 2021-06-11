#!coding:utf8

#author:yqq
#date:2020/9/17 0017 18:37
#description:
import datetime
import random,time
import numpy as np 
from concurrent import futures
import logging
import yaml
from multiprocessing import Process, cpu_count

from impl.header_ex_api import HuoBi, OKEX
from impl.sms import juhe_cn_send_sms
from sdks.tokencan import TokenCanWrapper
from utils import round_down_float_all
from concurrent.futures import ProcessPoolExecutor,  ALL_COMPLETED



class TradeSide:
    BUY = 'BUY'
    SELL = 'SELL'

class OrderBooker:
    def __init__(self, config_path : str, symbol: str):
        # # 读取配置文件

        with open(config_path, 'r', encoding='UTF-8') as f:
            self.conf = yaml.safe_load(f.read())

        conf = self.conf
        self.envpath = conf[symbol]['envpath']
        self.amount_precision = conf[symbol]['AmountPrecision']
        self.PricePrecision = conf[symbol]['PricePrecision']
        self.kind = False

        self.tradesymbol = conf[symbol]['tradesymbol']
        self.maxpricerate = conf[symbol]['maxpricerate']
        self.Flwsymbol = conf[symbol]['Flwsymbol']
        self.FlwMul = conf[symbol]['FlwMul']
        self.FlwExchange = conf[symbol]['FlwExchange']
        self.period = conf[symbol]['period']

        self.IsOpen = conf[symbol]['orderbook']['IsOpen']

        self.order_amount_min = conf[symbol]['orderbook']['order_amount_min']
        self.order_amount_max = conf[symbol]['orderbook']['order_amount_max']
        self.delay = conf[symbol]['orderbook']['delay']
        self.Rg = conf[symbol]['orderbook']['Rg']
        self.ordernum = conf[symbol]['orderbook']['ordernum']

        self.akey = conf[symbol]['orderbook']['akey']
        self.skey = conf[symbol]['orderbook']['skey']

        self.phone_numbers = conf[symbol]['phone_number']
        self.phone_text_tpl_id = conf[symbol]['phone_text_tpl_id']
        self.phone_text_key = conf[symbol]['phone_text_key']

        self.tc = TokenCanWrapper(akey=self.akey, skey=self.skey)

        self.hb = HuoBi()
        self.okex = OKEX()

        pass



    # 依次下单 param 下单方向 下单价格数量列表 下单间隔时间
    def submit_orders(self, side : str, orders: list, dealy: float):
        assert  side in [TradeSide.BUY, TradeSide.SELL] , 'side is invalid!!!'
        if len(orders) == 0: return  []

        ret = []
        trade_func =  self.tc.buy_in_limit_price if side == TradeSide.BUY else self.tc.sell_in_limit_price
        for ord in orders:
            try:
                print('下{}单数据:{}'.format(side, ord))
                o_b = trade_func(self.tradesymbol, ord[0], ord[1])
                ret.append(o_b)
            except Exception as e:
                print('下单错误:{}, order:{}'.format(e, ord))
                pass
            time.sleep(dealy)
        print('成功下{}单, {}笔'.format(side, len(orders)))
        return ret


    # 得到目标价
    def get_base_price(self):
        try:
            # 目标涨跌幅
            if self.FlwExchange == 'Okex':
                fkline = self.okex.GetRate(self.Flwsymbol, self.period)
                T_rate = fkline['OK_rate']
                if T_rate <= -1:
                    # Logging.info(tradesymbol+' 得到目标价错误')
                    raise Exception(self.tradesymbol+' 得到目标价错误')
                ticker = self.tc.get_ticker(symbol=self.tradesymbol)
                nowprice = ticker['last']
                return (float(nowprice) * (1 + self.FlwMul * T_rate))
            elif self.FlwExchange == 'HuoBi':
                fkline = self.hb.GetRate(self.Flwsymbol, self.period)
                T_rate = fkline['HB_rate']
                if T_rate <= -1:
                    # Logging.info(tradesymbol+' 得到目标价错误')
                    raise Exception(self.tradesymbol+' 得到目标价错误')

                # 昨天的收盘价作为今天基准价
                open_price = self.tc.get_base_price(symbol=self.tradesymbol, period=self.period)
                return (float(open_price) * (1 + self.FlwMul * T_rate))
            else:
                raise Exception("未知交易所 FlwExchange : {0}".format(self.FlwExchange))

        except Exception as e:
            # Logging.info(tradesymbol+' 得到目标价错误:{}'.format(e))
            print('得到目标价错误: {}'.format(e))
            raise e
            # return -1

    # 得到下单列表
    def make_orders(self) -> tuple:
        # 挂单核心逻辑 by aether 2020年4月4日20:01:05
        nowprice = self.get_base_price()

        # 这个rg建议是随机浮动
        minprice = nowprice * (1 - self.Rg)
        maxprice = nowprice * (1 + self.Rg)

        # Logging.info(tradesymbol+' nowprice:{}'.format(nowprice))

        # 得到买单下单价列表
        bprice = np.random.uniform(minprice, nowprice, self.ordernum)
        buypricelist = round_down_float_all(list(bprice), self.PricePrecision)

        # 得到数量列表
        bamount = np.random.uniform(self.order_amount_min, self.order_amount_max, self.ordernum)
        buyamountlist = round_down_float_all(list(bamount), self.amount_precision)

        buyorderlist = list(zip(buypricelist, buyamountlist))
        # Logging.info('Buy下单列表:{}'.format(buyorderlist))

        # 得到下单价列表
        sprice = np.random.uniform(nowprice, maxprice, self.ordernum)
        sellpricelist = round_down_float_all(list(sprice), self.PricePrecision)
        # 得到数量列表
        samount = np.random.uniform(self.order_amount_min, self.order_amount_max, self.ordernum)
        sellamountlist = round_down_float_all(list(samount), self.amount_precision)

        sellorderlist = list(zip(sellpricelist, sellamountlist))
        # Logging.info('Sell下单列表:{}'.format(sellorderlist))
        return buyorderlist, sellorderlist


    def cancel_timeout_orders(self, ord_lifetime_secs: int, per_op_delay: float, page_size: int=100):
        o_ids = []
        nowtime = int(time.time())
        assert isinstance(self.tc, TokenCanWrapper), 'tc is not  TokenCanWrapper'
        orders = self.tc.get_orders(self.tradesymbol, page_size=page_size)
        # print("订单笔数: {}".format( len(orders)) )

        if len(orders) < 50:
            print('挂单笔数小于50, 暂时不撤单')
            return

        random.shuffle(orders)
        this_symbol_orders = []
        for order in orders:
            order_symbol = str(order['baseCoin'].strip() + order['countCoin'].strip()).lower()
            o_time = int(int(order['created_at']) / 1000)
            if nowtime - o_time < ord_lifetime_secs: 
                print('{} - {} < {}, 跳过这笔订单'.format(nowtime, o_time, ord_lifetime_secs))
                continue
            if order_symbol != self.tradesymbol:
                print('交易对不匹配{} != {}'.format(order_symbol, self.tradesymbol))
                continue
            this_symbol_orders.append(order)
        print("准备撤单:{}笔".format(len(this_symbol_orders)))

        random.shuffle(this_symbol_orders)
        count = 0
        failed_count = 0
        for i in range(len(this_symbol_orders)):
            order_id = this_symbol_orders[i]['id']
            try:
                rsp = self.tc.cancel_order(self.tradesymbol, order_id)
                logging.info("撤单结果：{}\n撤单信息：{}".format(rsp, order_id))
                time.sleep(per_op_delay)
                count += 1
            except Exception as e:
                print('订单:{}, 撤单失败. {}'.format(order_id, e))
                failed_count += 1

        print('成功撤单:{} 笔, 失败 {}'.format(count, failed_count))


    # 撤销超时未成交订单
    def cancel_timeout_orders_loop(self, ord_lifetime_secs: int = 60,
                                   per_op_delay: float = 0.05,
                                   per_loop_delay: float = 15):
        while True:
            try:
                self.cancel_timeout_orders(ord_lifetime_secs, per_op_delay)
            except Exception as e:
                # Logging.exception('执行撤单错误:{}'.format(e))
                print('执行撤单错误:{}'.format(e))
            time.sleep( per_loop_delay )


    def trade_loop(self, per_loop_interval_secs: float = 5.0):
        proc_executor = ProcessPoolExecutor(max_workers=2) #一个进程铺卖单, 一个进程铺买单
        while True:
            try:
                buyorderlist, sellorderlist =  self.make_orders()


                fs = []
                future_buy = proc_executor.submit(self.submit_orders, TradeSide.BUY, buyorderlist, self.delay)
                fs.append(future_buy)

                future_sell = proc_executor.submit(self.submit_orders, TradeSide.SELL, sellorderlist, self.delay)
                fs.append(future_sell)


                #future_cancel = proc_executor.submit(self.cancel_timeout_orders_loop, 60,  1, 10)
                #fs.append(future_cancel)

                futures.wait(fs=fs, timeout=50, return_when=ALL_COMPLETED)
                for f in fs:
                    if not f.done():
                        f.cancel()

                self.cancel_timeout_orders(60, 1, 160)
            except Exception as e:
                # Logging.exception('执行下单错误:{}'.format(e))
                print('执行下单错误:{}'.format(e))
                pass

            time.sleep(per_loop_interval_secs)


    def monitor_balance_loop(self):
        last_sms_time = 0
        while True:
            try:
                now = datetime.datetime.now()
                is_timed = (now.hour == 10 and now.minute == 0) or (now.hour == 22 and now.minute == 0)
                if not is_timed:  # 上午10点, 晚上22点
                    time.sleep(20)
                    continue

                if isinstance(last_sms_time, datetime.datetime):
                    d = now - last_sms_time
                    if d.seconds < 120:  #整点时发短信频率间隔两分钟以上, 防止到点时发送多条短信
                        time.sleep(5)
                        continue

                last_sms_time = 0
                balances = self.tc.get_account_balance(symbols=['htdf', 'usdt'])
                assert len(balances) == 2, 'balances length is not equals 2'

                htdf_normal_balance = int(float(balances['htdf']['normal']))
                htdf_locked_balance = int(float(balances['htdf']['locked']))
                usdt_normal_balance = int(float(balances['usdt']['normal']))
                usdt_locked_balance = int(float(balances['usdt']['locked']))

                params = {
                    "mobile": self.phone_numbers,
                    "tpl_id": self.phone_text_tpl_id,
                    "key": self.phone_text_key
                }
                name = '\n【{} 资金监控】\n'.format('T網机器人')
                content = 'H普通余额为{}，冻结余额为{}；U普通余额为{}，冻结余额为{}，{}。' \
                    .format(htdf_normal_balance, htdf_locked_balance,
                            usdt_normal_balance, usdt_locked_balance, datetime.datetime.now())
                params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
                juhe_cn_send_sms(msg=params)

                last_sms_time = datetime.datetime.now()

            except Exception as e:
                print('monitor_balance_loop: {}'.format(e))

            # time.sleep(12 * 60 * 60)
            pass

    def startloop(self):
        """
        阻塞
        :return:
        """

        # 撤销所有订单
        ### self.tc.cancel_all_orders( symbol=self.tradesymbol )


        # 撤单进程
        cancel_process = Process(target=self.cancel_timeout_orders_loop,
                                 kwargs={'ord_lifetime_secs': 60,
                                         'per_op_delay': 0.5,
                                         'per_loop_delay':10})

        cancel_process.daemon = True  #主进程退出, 子进程自动退出
        cancel_process.start()


        #监控机器人 HTDF  USDT 余额, 每隔一个小时发一次短信
        sms_balance_monitor_process = Process(target=self.monitor_balance_loop)
        sms_balance_monitor_process.daemon = True
        sms_balance_monitor_process.start()


        #在主进程中进行创建子进程
        self.trade_loop( per_loop_interval_secs=10)
        cancel_process.join()



if __name__ == '__main__':

    ob = OrderBooker(config_path='../config.yml', symbol='HTDF/USDT')
    ob.startloop()

    pass
