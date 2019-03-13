import logging
import time

import requests

from config import dev_mode, send_index_url
from utils import send_warning_email
from WX.wx_login import WX


def parse_index_data(index_data: dict):
    if not index_data:
        return None
    index_list = index_data.get('data', {}).get('wxindex', '').split(',')
    if not index_list:
        return None
    print(f'index_data -> {index_data}')
    current_index = index_list[-1]
    pre_day_index = index_list[-2]
    index_variation = int(current_index) - int(pre_day_index)
    index_variance_ratio = round(index_variation / int(pre_day_index), 4)
    return {
        'wx_index': {
            'name': '微信区块链指数',
            'index_variation': index_variation,
            'current_index': current_index,
            'index_variance_ratio': index_variance_ratio
        }
    }


def post_gbi_index(index):
    # 发送给后端
    pass


def wx_spider():
    wx = WX()
    wx_status = False
    while True:
        if wx_status:
            time.sleep(10)
        logging.info(f'开始获取')
        index = wx.get_index()
        if not index or (index.get('retcode') == -1):
            wx.is_login = False
            continue
        logging.info(f'index -> {index}')
        wx_status = wx.is_login
        time.sleep(20)
        post_gbi_index(parse_index_data(index))


if __name__ == '__main__':
    wx_spider()
