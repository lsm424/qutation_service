# encoding=utf-8
import collections
import re
import time
from functools import reduce

from common.conf import conf
from common.log import logger
from qutation_api.base import Base


class Sina(Base):
    """新浪免费行情获取"""

    grep_detail = re.compile(
        r"(\d+)=[^\s]([^\s,]+?)%s%s"
        % (r",([\.\d]+)" * 29, r",([-\.\d:]+)" * 2)
    )
    grep_detail_with_prefix = re.compile(
        r"(\w{2}\d+)=[^\s]([^\s,]+?)%s%s"
        % (r",([\.\d]+)" * 29, r",([-\.\d:]+)" * 2)
    )
    del_null_data_stock = re.compile(
        r"(\w{2}\d+)=\"\";"
    )

    def __init__(self):
        batch_size = conf.getint('新浪', 'batch_size')
        super(Sina, self).__init__(batch_size, '新浪')
        self._headers.update({
            'Referer': 'http://finance.sina.com.cn/'
        })

    def get_stock_api(self, stocks: str) -> str:
        url = f"http://hq.sinajs.cn/rn={int(time.time() * 1000)}&list={stocks}"
        for i in range(3):
            try:
                r = self._session.get(url, headers=self._headers, timeout=0.3)
                # logger.debug(f'新浪api耗时：{r.elapsed}, 股票数量：{len(stocks)}')
                return r.text
            except BaseException as e:
                logger.error(f'发送获取新浪行情数据失败: {e}')
        return None

    def format_response_data(self, stocks_detail: str):
        # stocks_detail = self.del_null_data_stock.sub('', "".join(rep_data)).replace(' ', '')
        # if not stocks_detail:
        #     logger.error(f'无新浪行情数据，无法组装')
        #     return {}
        # stocks_detail = "".join(rep_data)
        if not stocks_detail:
            # logger.error('无新浪行情数据，无法组装')
            return {}
        result = self.grep_detail_with_prefix.finditer(stocks_detail)
        stock_dict = reduce(lambda x, y: x | y, map(lambda x: {x[0]: {
            'name': x[1],       #
            'code': x[0],
            'open': x[2],    # 当日
            'close': x[3],
            'now': x[4],
            'high': x[5],
            'low': x[6],
            # 'buy': x[7],
            # 'sell': x[8],
            'volume': int(x[9]),
            'turn_over': int(float(x[10])),
            'bid1_volume': int(x[11]),
            'bid1': x[12],
            'bid2_volume': int(x[13]),
            'bid2': x[14],
            'bid3_volume': int(x[15]),
            'bid3': x[16],
            'bid4_volume': int(x[17]),
            'bid4': x[18],
            'bid5_volume': int(x[19]),
            'bid5': x[20],
            'ask1_volume': int(x[21]),
            'ask1': x[22],
            'ask2_volume': int(x[23]),
            'ask2': x[24],
            'ask3_volume': int(x[25]),
            'ask3': x[26],
            'ask4_volume': int(x[27]),
            'ask4': x[28],
            'ask5_volume': int(x[29]),
            'ask5': x[30],
            'time': x[31] + ' ' + x[32],
        }}, map(lambda x: x.groups(), result)))
        # logger.info(f'新浪行情数据：{list(stock_dict.keys())[:10]}...')
        return stock_dict


if __name__ == '__main__':
    api = Sina()
    ret = api.market_snapshot('sh600227')
    import json
    print(json.dumps(ret))