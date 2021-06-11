#!coding:utf8

#author:yqq
#date:2020/9/17 0017 18:37
#description:

# 截断小数点位数
from typing import Union, List, Tuple
from copy import deepcopy


def round_down_float(num, precision):
    if precision == 0:
        return int(num)
    decimal = 10 ** precision
    assert decimal != 0 , 'decimal is 0!!'
    data = int(num * decimal)
    return data / decimal



# 整个数组截取小数点位数
def round_down_float_all(array : Union[List, Tuple] , precision : int):
    if len(array) == 0:
        return  array
    a = deepcopy(array)
    for i in range(len(a)):
        a[i] = round_down_float(a[i], precision)
    return a