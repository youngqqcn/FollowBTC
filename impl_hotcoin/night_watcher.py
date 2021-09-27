#coding:utf8
import time
import threading
import json
import urllib
import urllib.request as req
import yaml
import os
from urllib.parse import urlencode

from concurrent.futures.thread import ThreadPoolExecutor
executor_ = ThreadPoolExecutor(max_workers=10)


# ��ȡ�����ļ�
def ReadCfg(symbol):
    global AmountPrecision, PricePrecision, envpath, order_amount_min, order_amount_max, \
        high_price, low_price,trade_coin_asset_alarm,base_coin_asset_alarm,init_asset_trade_coin,\
        init_asset_base_coin, phone_number, phone_text_tpl_id, phone_text_key, huge_quantity_order,\
        low_volume_trade_alarm,over_price_space_alarm,price_amplitude_alarm,trade_record_alarm,\
        trade_record_alarm_time_scale,current_asset_alarm,depth_one_two_price_alarm,low_volume_order_alarm,\
        huge_quantity_order_alarm,this_symbol, alarm_sleep_time, low_volume_trade_value,\
        price_amplitude_value, depth_one_two_price_value

    path = os.path.join(os.path.dirname(__file__), 'baseconf.yml')
    with open(path, 'r', encoding='UTF-8') as f:
        conf = yaml.safe_load(f.read())

    depth_one_two_price_value = conf[symbol]['depth_one_two_price_value']
    price_amplitude_value = conf[symbol]['price_amplitude_value']
    low_volume_trade_value = conf[symbol]['low_volume_trade_value']
    huge_quantity_order_alarm = conf[symbol]['huge_quantity_order_alarm']
    low_volume_order_alarm = conf[symbol]['low_volume_order_alarm']
    depth_one_two_price_alarm = conf[symbol]['depth_one_two_price_alarm']
    current_asset_alarm = int(conf[symbol]['current_asset_alarm'])
    trade_record_alarm_time_scale = conf[symbol]['trade_record_alarm_time_scale']
    trade_record_alarm = conf[symbol]['trade_record_alarm']
    price_amplitude_alarm = conf[symbol]['price_amplitude_alarm']
    over_price_space_alarm = conf[symbol]['over_price_space_alarm']
    low_volume_trade_alarm = conf[symbol]['low_volume_trade_alarm']

    trade_coin_asset_alarm = conf[symbol]['trade_coin_asset_alarm']
    base_coin_asset_alarm = conf[symbol]['base_coin_asset_alarm']
    init_asset_trade_coin = conf[symbol]['init_asset_trade_coin']
    init_asset_base_coin = conf[symbol]['init_asset_base_coin']

    phone_number = conf[symbol]['phone_number']
    phone_text_tpl_id = conf[symbol]['phone_text_tpl_id']
    phone_text_key = conf[symbol]['phone_text_key']
    huge_quantity_order = conf[symbol]['huge_quantity_order']

    AmountPrecision = conf[symbol]['AmountPrecision']  # �µ���������
    PricePrecision = conf[symbol]['PricePrecision']  # �µ��۸񾫶�
    # order_amount_min = conf[symbol]['order_amount_min']  # �ҵ���ʼ������Сֵ
    # order_amount_max = conf[symbol]['order_amount_max']  # �ҵ���ʼ�������ֵ
    high_price = conf[symbol]['HighPrice']
    low_price = conf[symbol]['LowPrice']
    envpath = conf[symbol]['envpath']
    this_symbol = conf[symbol]['this_symbol']
    alarm_sleep_time = conf[symbol]['alarm_sleep_time']


def warn_analysis(trade_coin_asset_init, base_coin_asset_init, assets):
    params = {
        "mobile": phone_number,  # ���ܶ��ŵ��û��ֻ�����
        "tpl_id": phone_text_tpl_id,  # ������Ķ���ģ��ID������ʵ������޸�
        "key": phone_text_key  # Ӧ��APPKEY(Ӧ����ϸҳ��ѯ)
    }
    name = '\n��{} �ʽ��ء�\n'.format(this_symbol)
    # params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
    # send_alarm_content(params)
    coin_list = this_symbol.split("/")
    for asset in assets:
        asset = asset.body
        avai_asset = round(float(asset.get("availVol")), 8)
        freeze_asset = round(float(asset.get("freezeVol")), 8)
        total = round(avai_asset + freeze_asset, 8)
        coin_name = asset.get("coin")
        if coin_name == coin_list[0]:
            if total < trade_coin_asset_init * trade_coin_asset_alarm and current_asset_alarm == 1:
                content = "\n��ǰ�ʽ�\n{}��{}\n��ʼ�ʽ�\n{}:{}".format(coin_name, total, coin_name, trade_coin_asset_init)
                params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
                send_alarm_content(params)
                send_alarm_voice()
        if coin_name == coin_list[1]:
            if total < base_coin_asset_init * base_coin_asset_alarm and current_asset_alarm == 1:
                content = "\n��ǰ�ʽ�\n{}��{}\n��ʼ�ʽ�\n{}:{}".format(coin_name, total, coin_name, base_coin_asset_init)
                params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
                send_alarm_content(params)
                send_alarm_voice()

def asset_alarm():
    """
    �ʽ���
    :return:
    """
    print("�ʽ���������....")
    # ��ȡ��ʼ���ʲ�
    trade_coin_asset_init, base_coin_asset_init = InitAsset()
    # ��ȡ�������
    if not trade_coin_asset_init or not base_coin_asset_init:
        pass
    assets = None.get_symbol_assets(this_symbol)  #TODO: �滻��Ŀ�꽻������ʵ��
    print(str(assets))
    # Ԥ���ж��߼� True/False
    warn_analysis(trade_coin_asset_init, base_coin_asset_init, assets)

def trade_record_alarm_start():
    """
    ���׼�¼���
    1. ��ȡ���³ɽ���¼
    2. �͵�ǰʱ��Ƚ�
    3. ����10����δ���ף����Ͷ���/�绰Ԥ��
    :return:
    """
    print("���׼�¼���������....")
    # ��ȡ���³ɽ���¼
    last_trade_list = None.GetTradeList(this_symbol + '.trade')   #TODO: �滻��Ŀ�꽻������ʵ��
    # Ԥ���߼�
    # ����10����δ���ף����Ͷ���/�绰Ԥ��
    trade_record_analysis(last_trade_list)

def trade_record_analysis(last_trade_list):
    """
    ����˵����
        1. �����ɽ����
        2. �۸񲨶��쳣Ԥ��
            2.1 ������߼ۺ���ͼ�
            2.2 ����20���ɽ���¼�۸��������5%��
        3. �޳ɽ���¼Ԥ��������Ԥ�����ʱ��
    """
    params = {
        "mobile": phone_number,  # ���ܶ��ŵ��û��ֻ�����        "tpl_id": phone_text_tpl_id,  # ������Ķ���ģ��ID������ʵ������޸�
        "tpl_id": phone_text_tpl_id,
        "key": phone_text_key  # Ӧ��APPKEY(Ӧ����ϸҳ��ѯ)
    }
    name = '��{} �̿ڳɽ���ء�'.format(this_symbol)
    price_list = []
    for trade_record in last_trade_list:
        trade_price = float(trade_record.get('price'))
        trade_volume = float(trade_record.get('volume'))
        # �����ɽ����  �������û�
        if trade_volume < low_volume_trade_value and low_volume_trade_alarm == 1:
            content = '��ǰ�̿��е����ɽ������ע'
            params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
            send_alarm_content(params)
            send_alarm_voice()
        # �۸񳬹���߼ۺ���ͼۼ��
        if trade_price > high_price or trade_price < low_price:
            content = '��ǰ�ɽ��۸񳬹��趨����߼ۺ���ͼۣ��뼰ʱ����'
            params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
            if over_price_space_alarm == 1:
                send_alarm_content(params)
                send_alarm_voice()
        # ����20���ɽ���¼�۸��������5%��
        price_list.append(trade_price)
    max_price = max(price_list)
    min_price = min(price_list)
    # amplitude: ���
    amplitude = round((max_price - min_price)/min_price, 5)
    if amplitude >= price_amplitude_value/100.0 and price_amplitude_alarm == 1:
        content = '����������󣨳���{}%�������ע'.format(price_amplitude_value)
        params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
        send_alarm_content(params)
        send_alarm_voice()
    # �޳ɽ���¼Ԥ��������Ԥ�����ʱ��
    time_scale = int(time.time()) - int(last_trade_list[0].get('time')[:10])
    if time_scale > trade_record_alarm_time_scale and trade_record_alarm == 1:
        content = '�̿�{}���ڣ��޳ɽ���¼���뼰ʱ����'.format(trade_record_alarm_time_scale)
        params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
        send_alarm_content(params)
        send_alarm_voice()
        time.sleep(alarm_sleep_time)

def InitAsset():
    try:
        # Logging.info('��ʼ���ʲ�')
        init_assets = None.get_symbol_assets(this_symbol)    #TODO: �޸ĳ�Ŀ�꽻����ʵ��

        if not init_assets:
            return None, None
        for asset in init_assets:
            asset = asset.body
            avail_asset = round(float(asset.get("availVol")), 8)
            freeze_asset = round(float(asset.get("freezeVol")), 8)
            total_asset = round(avail_asset + freeze_asset, 8)
            coin_name = asset.get("coin")

            # ���뵽���ݿ⣨�־û���
            # �߼���������ݿ���������ʲ��ļ�¼���򲻸���

        return init_asset_trade_coin, init_asset_base_coin
    except Exception as e:
        # Logging.exception('��ʼ���ʽ����:{}'.format(e))
        pass

def send_alarm_voice():
    """
    ����˵����
        ������������
    :return:
    """
    host = 'http://yuyintz.market.alicloudapi.com'
    path = '/ts/voiceNotifySms'

    # params = urlencode()
    phone_number_list = phone_number.split(",")
    for phone_num in phone_number_list:
        # querys = 'mobile={}&tpl_id=TP20041710'.format(phone_num)
        querys = 'mobile={}&tpl_id=TP20042211'.format(phone_num)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Authorization": "APPCODE 0b0321966ad2425abc4bbde57f1c0f8d"
        }
        url = host + path + '?' + querys
        request_param = req.Request(url=url, method='POST', headers=headers)
        response = req.urlopen(request_param)
        content = response.read()
        if (content):
            print(content)

def send_alarm_content(msg):
    r"""ģ�壺
    �����ϵͳ��
msg:
{
'mobile':'',
'tpl_id':'',
'tpl_value':'',
'key':''
}
"""


    url = "http://v.juhe.cn/sms/send"
    mobile_phone_list = msg.get("mobile").split(",")
    for phone_number in mobile_phone_list:
        msg['mobile'] = phone_number
        params = urlencode(msg)
        f = urllib.request.urlopen(url+"?"+params)
        content = f.read()
        res = json.loads(content)
        if res:
            # Logging.info("���ͳɹ�{}".format(res))
            pass
        else:
            # Logging.info("�����쳣{}".format(res))
            pass

def quote_date_analysis(quote_date):
    """
    С���̿������ز���
    """
    params = {
        "mobile": phone_number,  # ���ܶ��ŵ��û��ֻ�����
        "tpl_id": phone_text_tpl_id,  # ������Ķ���ģ��ID������ʵ������޸�
        "key": phone_text_key  # Ӧ��APPKEY(Ӧ����ϸҳ��ѯ)
    }
    name = '��������ݼ�ء�'
    # params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
    # send_alarm_content(params)
    asks = quote_date.get("asks")
    bids = quote_date.get("bids")
    # ��һ�������һ�����۲���
    buy_one_two_price_diff = round(float(bids[0].get("price"))-float(bids[1].get("price")), PricePrecision)
    sell_one_two_price_diff = round(float(asks[1].get("price"))-float(asks[0].get("price")), PricePrecision)
    buy_one_sell_one_price_diff = round(float(asks[0].get("price")) - float(bids[0].get("price")), PricePrecision)
    if buy_one_two_price_diff/buy_one_sell_one_price_diff > depth_one_two_price_value or sell_one_two_price_diff/buy_one_sell_one_price_diff > depth_one_two_price_value:
        # ��һ����۸�����һ��һ�̿ڼ۸���ֵ���������ֵ������Ԥ��
        print("��һ�������һ�����۸��쳣")
        content = '��һ�������һ�����۸��쳣'
        params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
        if depth_one_two_price_alarm == 1:
            send_alarm_content(params)
            send_alarm_voice()
    # �̿�С���ҵ����
    temp_quote = bids[:10] + asks[:10]
    for element in temp_quote:
        if float(element.get("volume")) < low_volume_trade_value:
            print("�̿ڹҵ����쳣���е���С���ҵ������ע")
            content = '�̿ڹҵ����쳣���е���С���ҵ������ע'
            params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
            if low_volume_order_alarm == 1:
                send_alarm_content(params)
                send_alarm_voice()
                break
    # �̿ھ����ҵ����
    # ������Ҳ����Ϊ����
    # �Ż���Ҫ�ų��������˵ĵ�
    temp_quote = bids[:100] + asks[:100]
    for element in temp_quote:
        # ����Ϊ����
        if round(float(element.get("volume"))*float(element.get("price")), 0) > huge_quantity_order:
            print("�̿ڹҵ����쳣���о����ҵ������ע")
            content = '�̿ڹҵ����쳣���о����ҵ������ע'
            params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
            if huge_quantity_order_alarm == 1:
                send_alarm_content(params)
                send_alarm_voice()
                break

def quote_alarm():
    """
    ����˵����
        ������
    """
    print("������������....")
    # ��ȡ���³ɽ���¼
    quote_date = None.GetQuote(this_symbol)    #TODO: �滻��Ŀ�꽻������ʵ��
    # Ԥ���߼�
    # ����10����δ���ף����Ͷ���/�绰Ԥ��
    quote_date_analysis(quote_date)

def _AssetAlarmStart():
    # print("-----------------�������ϵͳ------------------")
    # Logging.info('�ʽ�������......')
    InitAsset()
    while True:
        try:
            AssetAlarmStart()
            print("�ʽ���˯��:{}".format(alarm_sleep_time))
            time.sleep(alarm_sleep_time)
        except Exception as e:
            # Logging.exception('�ʽ����쳣:{}'.format(e))
            pass

def _QuoteAlarmStart():
    # print("-----------------�������ϵͳ------------------")
    # Logging.info('�����ؼ������......')
    while True:
        try:
            QuoteAlarmStart()
            print("������˯��:{}".format(alarm_sleep_time))
            time.sleep(alarm_sleep_time)
        except Exception as e:
            # Logging.exception('�����ؼ���쳣:{}'.format(e))
            pass

def _TradeAlarmStart():
    # print("-----------------�������ϵͳ------------------")
    # Logging.info('���׼������......')
    while True:
        try:
            TradeAlarmStart()
            print("���׼��˯��:{}".format(alarm_sleep_time))
            time.sleep(alarm_sleep_time)
        except Exception as e:
            # Logging.exception('���׼���쳣:{}'.format(e))
            pass

# ִ�м��
def AssetAlarmStart():
    try:
        # �ʽ���
        asset_alarm()
    except Exception as e:
        # Logging.exception('�ʽ����쳣:{}'.format(e))
        pass

def QuoteAlarmStart():
    try:
        # �����쳣���
        quote_alarm()
    except Exception as e:
        # Logging.exception('�������쳣:{}'.format(e))
        pass

def TradeAlarmStart():
    try:
        # ���׼�¼���  ��ȡ�������׼�¼���ݣ��̿ڵĽ��׼�¼���������ǻ������˻��ģ�
        trade_record_alarm_start()
    except Exception as e:
        # Logging.exception('���׼���쳣:{}'.format(e))
        pass


class RobAlarm(object):
    """docstring for OrderBook_HC"""

    def __init__(self, symbol):
        super(RobAlarm, self).__init__()
        self.symbol = symbol
        ReadCfg(self.symbol)

        # global het
        # het = CHet(envpath)
        # scheduler = BackgroundScheduler()

        # scheduler.add_job(CancelOrdersOutTime, 'interval', seconds=15)
        # scheduler.start()

        AssetAlarm_Thread = threading.Thread(target=_AssetAlarmStart)
        QuoteAlarm_Thread = threading.Thread(target=_QuoteAlarmStart)
        TradeAlarm_Thread = threading.Thread(target=_TradeAlarmStart)
        AssetAlarm_Thread.setDaemon(True)
        QuoteAlarm_Thread.setDaemon(True)
        TradeAlarm_Thread.setDaemon(True)
        AssetAlarm_Thread.start()
        QuoteAlarm_Thread.start()
        TradeAlarm_Thread.start()