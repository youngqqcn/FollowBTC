#!coding:utf8

#author:yqq
#date:2020/9/21 0021 14:28
#description:
import json
from urllib.parse import quote, urlencode
from urllib.request import urlopen


__all__ = ['juhe_cn_send_sms']

def juhe_cn_send_sms(msg):
    """模板：
     【监控系统】
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
        f = urlopen(url+"?"+params)
        content = f.read()
        res = json.loads(content)
        if res:
            print("发送成功{}".format(res))
        else:
            print("请求异常{}".format(res))
#
# def main():
#
#     telno = '18273664901,18565659593'
#     #strcont = '【shbao】 尊敬的管理员，余额监控。{0}余额为{1}。'.format('HTDF', '243.2349234')
#     # sms_template = '【shbao】 尊敬的管理员，余额预警。{0}出币地址{1}余额为{2}，请立即充值{3}。{4},{5}' + 'T网机器人'
#     # sms_template.format('HTDF', 'HTDF', '12345.12345', 'HTDF', str(datetime.datetime.now()), 'PRO')
#     #
#     # send_sms(telno=telno, strcontent=sms_template)
#
#     params = {
#         "mobile": telno,  # 接受短信的用户手机号码        "tpl_id": phone_text_tpl_id,  # 您申请的短信模板ID，根据实际情况修改
#         "tpl_id": '213111' ,
#         "key": '315654922d9b6849cdf5e6bb2a23542c'  # 应用APPKEY(应用详细页查询)
#     }
#     name = '\n【{} 资金监控】\n'.format('HTDF')
#     content = '普通余额{}，冻结余额为{}。'.format('0.23', '19.23423')
#     params['tpl_value'] = "#name#={}&#content#={}".format(name, content)
#     juhe_cn_send_sms(msg=params)

#
#
#     pass
#
#
# if __name__ == '__main__':
#
#     main()