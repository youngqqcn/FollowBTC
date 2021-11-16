#!coding:utf8

# author:yqq
# date:2020/9/17 0017 18:18
# description:  画 K 线
# from impl import KlineTrader
from impl import KlineTrader


def main():
    kt = KlineTrader(config_path='./config.yml', symbol='NFCUSDT')
    kt.startloop()

    pass


if __name__ == '__main__':

    main()