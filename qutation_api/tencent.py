# encoding=utf-8
import collections
import re
from datetime import datetime
from functools import reduce
from typing import Optional

import numba

from common.conf import conf
from common.log import logger
from qutation_api.base import Base


class Tencent(Base):
    """腾讯免费行情获取"""

    grep_stock_code = re.compile(r"(?<=_)\w+")

    def __init__(self):
        batch_size = conf.getint('腾讯', 'batch_size')
        super(Tencent, self).__init__(batch_size, '腾讯')

    def get_stock_api(self, stocks: str) -> str:
        url = "http://qt.gtimg.cn/q=" + stocks
        for i in range(3):
            try:
                r = self._session.get(url, headers=self._headers, timeout=0.3)
                logger.debug(f'腾讯api耗时：{r.elapsed}, 股票数量：{len(stocks)}')
                return r.text
            except BaseException as e:
                logger.error(f'发送获取腾讯行情数据失败: {e}')
        return None

    @staticmethod
    def format_response_data(rep_data: str) -> dict:
        stock_details = map(lambda x: x.split("~"), rep_data.replace('"', '').split(";"))
        stock_details = filter(lambda x: len(x) > 49, stock_details)
        stock_dict = map(lambda x: {
                'name': x[1],  # 股票名称
                'code': x[0].split('=')[0].split('_')[-1],  # 股票
                'now': x[3],  # 当前价格
                'close': x[4],  # 昨日收盘价格
                'open': x[5],   # 当日开盘价格
                'volume': int(x[6]) * 100,    # 成交量
                # 'bid_volume': str(int(x[7]) * 100),  # 外盘
                # 'ask_volume': str(float(x[8]) * 100),    # 内盘
                'bid1': x[9],   # 买1
                'bid1_volume': int(x[10]) * 100,    # 买1量
                'bid2': x[11],   # 买2
                'bid2_volume': int(x[12]) * 100,    # 买2量
                'bid3': x[13],   # 买3
                'bid3_volume': int(x[14]) * 100,    # 买3量
                'bid4': x[15],   # 买4
                'bid4_volume': int(x[16]) * 100,    # 买4量
                'bid5': x[17],   # 买5
                'bid5_volume': int(x[18]) * 100,    # 买5量
                'ask1': x[19],   # 卖1
                'ask1_volume': int(x[20]) * 100,    # 卖1量
                'ask2': x[21],   # 卖2
                'ask2_volume': int(x[22]) * 100,    # 卖2量
                'ask3': x[23],   # 卖3
                'ask3_volume': int(x[24]) * 100,    # 卖3量
                'ask4': x[25],   # 卖4
                'ask4_volume': int(x[26]) * 100,    # 卖4量
                'ask5': x[27],   # 卖5
                'ask5_volume': int(x[28]) * 100,    # 卖5量
                # '最近逐笔成交': x[29],
                'time': f'{x[30][:4]}-{x[30][4:6]}-{x[30][6:8]} {x[30][8:10]}:{x[30][10:12]}:{x[30][12:14]}',
                # 'rise': x[31],   # 涨跌
                # 'rise(%)': x[32],  # 涨跌百分比
                'high': x[33],   # 最高
                'low': x[34],    # 最低
                'turn_over': int(x[35].split('/')[-1]),     # 成交额（元）
                # 'turn_over_1': x[35],     # 最新价/成交量（手）/成交额
                # '成交量(手)': int(x[36]) * 100,
                # '成交额(万)': x[37] * 10000,
                # 'turnover': x[38] if x[38] else None,   # 换手率
                # 'PE': x[39] if x[39] else None,     # ttm市盈率
                # 'unknown': x[40],
                # 'high_2': x[41],  # 意义不明
                # 'low_2': x[42],  # 意义不明
                # 'amplitude': x[43],     # 振幅
                # 'circulating_market_val': x[44] if x[44] else None,   # 流通市值
                # 'total_market_val': x[45] if x[45] else None,   # 总市值
                # 'PB': x[46],
                # 'limit_up_price': x[47],  # 涨停价
                # 'limit_down_price': x[48],      # 跌停价
                # 'volume_ratio': x[49] if x[49] else None,   # 量比
                # 'spread': x[50] if len(x) > 50 else None,   # 委差
                # 'average_price': x[51] if len(x) > 51 else None,    # 均价
                # 'PE_dynamic': x[52] if len(x) > 52 and x[52] else None,       # 市盈(动)
                # 'PE_static': x[53] if len(x) > 53 and x[53] else None,   # 市盈(静)
            }, stock_details)
        stock_dict = {x['code']: x for x in stock_dict}
        return stock_dict


if __name__ == '__main__':
    api = Tencent()
    ret = api.market_snapshot('sh600227')
    import json
    print(json.dumps(ret))