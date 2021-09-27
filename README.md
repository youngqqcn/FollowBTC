# Tokencan(T网)HTDF交易机器人

## 跟随策略
 跟随火币BTC涨跌幅

- `目标价 =  T网最新成交价 × 火币BTC日涨跌幅  × (1 + 涨跌幅系数) `
- `分钟成交量 = 火币BTC分钟成交量 × 成交量系数 `



## 运行环境

- Linux/Windows/MacOS
- Python3.6,  Python.3.7, Python3.8



## 安装依赖

`pip3 install requirements.txt `


## 运行

- `kline_trader_main.py` : 画K线 
- `order_book_main.py` : 铺买卖单


### 前台运行

```
python3  kline_trader_main.py
python3 order_book_main.py
```


### 后台运行

- 方式1: 直接使用 `make start`
- 方式2: 
```
nohup python3 -u kline_trader_main.py > all_prints.log 2>&1 &

nohup python3 -u order_book_main.py > all_prints.log 2>&1 &

```


## 停止

- 方式1: 使用 `make stop`
- 方式2: `ps aux | grep python3` 查看进程, 然后逐个 `kill`



## 配置文件 `config.yml`
修改`config.yml` 需要重启




## TODO:
- 报警




