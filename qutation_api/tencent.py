# encoding=utf-8
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
        super(Tencent, self).__init__(batch_size)

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
                'name': x[1],
                'code': x[0].split('=')[0].split('_')[-1],
                'now': float(x[3]),
                'close': float(x[4]),
                'open': float(x[5]),
                'volume': float(x[6]) * 100,
                'bid_volume': int(x[7]) * 100,
                'ask_volume': float(x[8]) * 100,
                'bid1': float(x[9]),
                'bid1_volume': int(x[10]) * 100,
                'bid2': float(x[11]),
                'bid2_volume': int(x[12]) * 100,
                'bid3': float(x[13]),
                'bid3_volume': int(x[14]) * 100,
                'bid4': float(x[15]),
                'bid4_volume': int(x[16]) * 100,
                'bid5': float(x[17]),
                'bid5_volume': int(x[18]) * 100,
                'ask1': float(x[19]),
                'ask1_volume': int(x[20]) * 100,
                'ask2': float(x[21]),
                'ask2_volume': int(x[22]) * 100,
                'ask3': float(x[23]),
                'ask3_volume': int(x[24]) * 100,
                'ask4': float(x[25]),
                'ask4_volume': int(x[26]) * 100,
                'ask5': float(x[27]),
                'ask5_volume': int(x[28]) * 100,
                '最近逐笔成交': x[29],
                'datetime': f'{x[30][:4]}-{x[30][4:6]}-{x[30][6:8]} {x[30][8:10]}:{x[30][10:12]}:{x[30][12:14]}',
                '涨跌': float(x[31]),
                '涨跌(%)': float(x[32]),
                'high': float(x[33]),
                'low': float(x[34]),
                '价格/成交量(手)/成交额': x[35],
                '成交量(手)': int(x[36]) * 100,
                '成交额(万)': float(x[37]) * 10000,
                'turnover': float(x[38]) if x[38] else None,
                'PE': float(x[39]) if x[39] else None,
                'unknown': x[40],
                'high_2': float(x[41]),  # 意义不明
                'low_2': float(x[42]),  # 意义不明
                '振幅': float(x[43]),
                '流通市值': float(x[44]) if x[44] else None,
                '总市值': float(x[45]) if x[45] else None,
                'PB': float(x[46]),
                '涨停价': float(x[47]),
                '跌停价': float(x[48]),
                '量比': float(x[49]) if x[49] else None,
                '委差': float(x[50]) if len(x) > 50 else None,
                '均价': float(x[51]) if len(x) > 51 else None,
                '市盈(动)': float(x[52]) if len(x) > 52 and x[52] else None,
                '市盈(静)': float(x[53]) if len(x) > 53 and x[53] else None,
            }, stock_details)
        stock_dict = {x['code']: x for x in stock_dict}
        return stock_dict
