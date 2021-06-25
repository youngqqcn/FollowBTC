#!coding:utf8

#author:yqq
#date:2020/9/17 0017 18:18
#description:  铺单
from impl import OrderBooker

def main():
    ob = OrderBooker(config_path='./config.yml', symbol='HTDF/USDT')
    ob.startloop()
    pass

if __name__ == '__main__':

    main()
