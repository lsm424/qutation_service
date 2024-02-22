#encoding=utf-8
import abc
import multiprocessing.pool as ppool
import re
import time
from functools import reduce
import os
import requests
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait

from common.conf import conf, update_conf
from common.log import logger


class Base:
    def __init__(self, batchsize=800):
        """
        初始化股票行情基类
        :param batchsize: 批量拉取的颗粒度大小
        """
        self._session = requests.session()
        self._headers = {
            "Accept-Encoding": "gzip, deflate, sdch",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/54.0.2840.100 "
                "Safari/537.36"
            ),
        }
        self.__executor = ThreadPoolExecutor(max_workers=30)
        # 支持拉取的股票代码列表，并标准格式化，去重
        stock_code_list = list(map(lambda x: x.strip(), conf.get('股票', 'stock_code_list').split(',')))
        stock_code_list = [self.__get_stock_type(code) + code[-6:] for code in stock_code_list]
        stock_code_list = list(set(stock_code_list))
        # 分批生成
        batch_cnt = int(len(stock_code_list) / batchsize) + 1
        self.__stock_code = [','.join(stock_code_list[x * batchsize: (x + 1) * batchsize]) for x in range(batch_cnt)]

    def market_snapshot(self, stocks=[]):
        """
        获取股票行情
        :param stocks: 指定股票代码列表，默认空表示所有股票代码
        :param prefix: 返回的股票代码是否带前缀
        :return: 字典，key为股票代码，value为股票行情数据
        """
        if not stocks:
            stocks = self.__stock_code
        elif not isinstance(stocks, list):
            stocks = [stocks]
        start1 = time.time()
        r = list(map(lambda x: self.__executor.submit(self.get_stock_api, x), stocks))
        r, _ = wait(r, return_when=ALL_COMPLETED)
        r = filter(lambda x: x, map(lambda x: x.result(), r))
        start2 = time.time()
        pool = ppool.ThreadPool(os.cpu_count())
        try:
            res = pool.map(self.format_response_data, r)
        finally:
            pool.close()
        r = reduce(lambda x, y: x | y, res)
        # r = self.format_response_data(r)
        logger.info(f'完成行情数据获取{len(r)}条，总耗时：{time.time() - start1}，网络耗时：{start2 - start1}，数据组装耗时：{time.time() - start2}')
        return r

    @abc.abstractmethod
    def format_response_data(self, rep_data):
        """
        格式化股票行情数据，子类实现
        :param rep_data:
        :param prefix:
        :return:
        """
        pass

    @property
    @abc.abstractmethod
    def get_stock_api(self, stocks: [str]):
        """
        根据股票代码获取行情 api
        """
        pass

    def __get_stock_type(self, stock_code: str):
        """判断股票ID对应的证券市场
        匹配规则
        ['50', '51', '60', '90', '110'] 为 sh
        ['00', '13', '18', '15', '16', '18', '20', '30', '39', '115'] 为 sz
        ['5', '6', '9'] 开头的为 sh
        ['8']开头为bj， 其余为 sz
        :param stock_code:股票ID, 若以 'sz', 'sh' 开头直接返回对应类型，否则使用内置规则判断
        :return 'sh' or 'sz'"""
        sh_head = ("50", "51", "60", "90", "110", "113", "118",
                   "132", "204", "5", "6", "9", "7")
        bj_head = ('8',)
        if stock_code.startswith(("sh", "sz", "zz", "bj")):
            return stock_code[:2]
        else:
            return "sh" if stock_code.startswith(sh_head) else 'bj' if stock_code.startswith(bj_head) else "sz"

    @staticmethod
    def update_stock_codes():
        """获取所有股票 ID 并更新配置文件"""
        response = requests.get("http://www.shdjt.com/js/lib/astock.js")
        stock_codes = re.findall(r"~([a-z0-9]*)`", response.text)
        update_conf('股票', 'stock_code_list', ','.join(stock_codes))