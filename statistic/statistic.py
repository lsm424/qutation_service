# encoding=utf-8
import io
import itertools
import json
import multiprocessing
from collections import namedtuple
import os
import threading
import time
from datetime import datetime
from queue import Queue
from itertools import groupby
import dask.array as da
from dask import delayed
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.font_manager import FontProperties

matplotlib.use('TkAgg')

from common.conf import conf
from common.log import logger
from statistic.model import QutationLogModel

font = FontProperties(fname='./common/STHeiti Light.ttc', size=10)

class StatisticManager:
    """
    推送数据统计分析管理类
    日志数据异步写库
    """
    QuotationInfo = namedtuple('QuotationInfo', ['client_name', 'client_id', 'opr', 'data', 'create_time',
                                                 'analysis_statue', 'analysis_desc', 'avg_time'],
                               defaults=('', '', None, '', None, QutationLogModel.ANA_SUCC, '', 0.0))
    cared_stocks = {'sz002291', 'sh000010', 'bj870199'}

    def __init__(self):
        self._torrlencance = conf.getfloat('websocket推送', 'push_interval_torrlencance')
        self._interval = conf.getint('websocket推送', 'push_interval')
        self._analysis_info = {}  # key：客户端标志，value：上次推送的QuotationInfo
        self._queue = Queue()
        self.__analysis_t = threading.Thread(target=self._analysis_thread)
        self.__analysis_t.setDaemon(True)
        self.__analysis_t.start()
        self.__report_t = threading.Thread(target=self._report_thread)
        self.__report_t.setDaemon(True)
        self.__report_t.start()
        self._opr_list = [QutationLogModel.OPR_PUSH, QutationLogModel.OPR_OFFLINE, QutationLogModel.OPR_SUBSCRIBE,
                          QutationLogModel.OPR_UNSUBSCRIBE]

    def push_qutation_log(self, client_name, client_id, opr, data=''):
        """
        对外接口，推送行情数据进行统计分析
        :param client_name: 客户端名称
        :param client_id: 客户端ID
        :param opr: 操作类型
        :param data: 操作数据
        :return:
        """
        if not client_name:
            logger.error('保存出错：客户端名称为空')
            return
        elif not client_id:
            logger.error('保存出错：客户端id为空')
            return
        elif opr not in self._opr_list:
            logger.error(f'保存出错：操作类型不支持, opr={opr}')
            return
        elif opr in [QutationLogModel.OPR_PUSH, QutationLogModel.OPR_SUBSCRIBE] and not data:
            logger.error(f'保存出错：操作数据为空')
            return
        quotation_info = self.QuotationInfo(client_name, client_id, opr, data, datetime.now())
        self._queue.put(quotation_info)

    def _analysis_thread(self):
        logger.info(f'保存行情操作日志线程启动')
        while True:
            data = [self._queue.get()]
            while not self._queue.empty():
                data.append(self._queue.get())

            data = list(map(lambda x: self._analysis_quotation(x), data))
            try:
                QutationLogModel.insert_many(data).execute()
                logger.info(f'写入操作数据{len(data)}条')
            except BaseException as e:
                logger.error(f'写入操作数据失败 {e}')

    def _report_thread(self):
        logger.info(f'数据统计报告线程启动')
        while True:
            err_data = QutationLogModel.select().where(QutationLogModel.analysis_statue != QutationLogModel.ANA_SUCC)
            interval_error_data = list(
                filter(lambda x: x.analysis_statue == QutationLogModel.ANA_ERROR_INTERVAL, err_data))

            total = QutationLogModel.select().count()

            avg_time_data = QutationLogModel.select(QutationLogModel.avg_time).where(QutationLogModel.avg_time > 0)
            avg_time_data = sum(map(lambda x: x.avg_time, avg_time_data)) / len(avg_time_data) if len(avg_time_data) else 0

            msg = f'''
----------------统计分析---------------
推送记录总数：{total}
推送时间超过规定间隔数：{len(interval_error_data)}
平均timestamp：{avg_time_data}'''
            logger.info(msg)
            time.sleep(30)

    def _analysis_quotation(self, quotation_info: QuotationInfo):
        """
        分析推送的行情
        :param quotation_info: 行情数据
        :return: 返回字典
        """
        pre_quotation_info = self._analysis_info.get(quotation_info.client_id, None)
        stocks = {}
        if quotation_info.opr == QutationLogModel.OPR_PUSH:
            # 计算缺失
            diff = (quotation_info.create_time - pre_quotation_info.create_time).total_seconds() - self._interval
            if diff > self._torrlencance:
                quotation_info = quotation_info._replace(analysis_statue=QutationLogModel.ANA_ERROR_INTERVAL)
                quotation_info = quotation_info._replace(analysis_desc=f'超过规定间隔（{self._interval}s）{diff}s')

            # 计算timestampe平均值
            stocks = self.cared_stocks
            if pre_quotation_info.opr == QutationLogModel.OPR_PUSH:
                stocks &= set(pre_quotation_info.data.keys()) & set(quotation_info.data.keys())
                avg_time = sum(map(lambda x: (datetime.strptime(quotation_info.data[x]['time'], '%Y-%m-%d %H:%M:%S') -
                                              datetime.strptime(pre_quotation_info.data[x]['time'], '%Y-%m-%d %H:%M:%S')).
                                   total_seconds(), stocks)) / len(stocks)
                quotation_info = quotation_info._replace(avg_time=avg_time)
            self._analysis_info[quotation_info.client_id] = quotation_info
        elif quotation_info.opr in (QutationLogModel.OPR_OFFLINE, QutationLogModel.OPR_UNSUBSCRIBE):
            del self._analysis_info[quotation_info.client_id]
        else:
            self._analysis_info[quotation_info.client_id] = quotation_info

        if quotation_info.opr == QutationLogModel.OPR_PUSH and stocks:
            quotation_info = quotation_info._replace(data=json.dumps({x: quotation_info.data[x] for x in stocks}))
            logger.info(f'stock: {stocks}')
        return quotation_info._asdict()

    @staticmethod
    def __calc(x: list[QutationLogModel]):
        interval = (x[1].create_time - x[0].create_time).total_seconds()
        data_a = json.loads(x[0].data.replace("'", '"'))
        data_b = json.loads(x[1].data)
        _res = [interval]
        for x in StatisticManager.cared_stocks:
            if x not in data_a or x not in data_b:
                _res.append(0.0)
                continue
            s_a_timestamp = datetime.strptime(data_a[x]['time'], '%Y-%m-%d %H:%M:%S')
            s_b_timestamp = datetime.strptime(data_b[x]['time'], '%Y-%m-%d %H:%M:%S')
            _res.append((s_b_timestamp - s_a_timestamp).total_seconds())
        return _res

    def show_push_interval_image(self):
        """
        生成推送间隔分布图
        """
        data = QutationLogModel.select().where(QutationLogModel.opr == QutationLogModel.OPR_PUSH).\
            order_by(QutationLogModel.create_time.asc())
        data = groupby(data, lambda x: x.client_id)
        res = []

        for _, models in data:
            a, b = itertools.tee(models)
            next(b, None)  # 把 b 的指针移到第二个元素
            res += list(map(self.__calc, zip(a, b)))

        res = list(zip(*res))
        # 使用 Seaborn 画直方图
        fig, ax = plt.subplots(1 + len(self.cared_stocks))
        sns.histplot(res[0], kde=True, ax=ax[0])
        ax[0].set_title('推送间隔分布图', fontproperties=font)
        ax[0].set_xlabel('间隔时间单位（s）', fontproperties=font)
        ax[0].set_ylabel('次数', fontproperties=font)

        for i, x in enumerate(self.cared_stocks):
            sns.histplot(res[1 + i], kde=True, ax=ax[1 + i])
            ax[1 + i].set_title(f'股票{x} timestamp间隔分布图', fontproperties=font)
            ax[1 + i].set_xlabel('间隔时间单位（s）', fontproperties=font)
            ax[1 + i].set_ylabel('次数', fontproperties=font)

        # 保存子图为图片
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='svg')
        buffer.seek(0)
        return buffer


statistic_manager = StatisticManager()
