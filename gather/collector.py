# encoding=utf-8
from functools import reduce
from itertools import groupby
import random
import time
from datetime import datetime, timedelta

from sqlalchemy import func
from gather.model import *
from common.conf import conf
from common.log import logger
from common.utils import delta
from qutation_api.sina import Sina
from qutation_api.tencent import Tencent
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, FIRST_COMPLETED, wait
from apscheduler.schedulers.background import BackgroundScheduler
from exchange_calendars import get_calendar
from apscheduler.triggers.cron import CronTrigger
import json

stock_calendar = get_calendar('XSHG')

scheduler = BackgroundScheduler()
scheduler.start()


def job():
    print("Job executed at:", datetime.datetime.now())


# 创建一个后台调度器
scheduler = BackgroundScheduler()
scheduler.start()


class Collector:
    def __init__(self, name, stock_no, triggers: list[CronTrigger]):
        self.name = name
        self.stock_no = stock_no
        self.qutation = Sina()
        # one_minute_times = list(map(lambda x: list(zip(x[:-1], x[1:])),
        #                             map(lambda x: delta(x[0], x[1]), one_minute_times)))
        for trigger in triggers:
            scheduler.add_job(self.do_job, trigger)
        # multi_minute_times = list(map(lambda x: (datetime.strptime(x[0], '%H:%M'), datetime.strptime(x[1], '%H:%M')),
        #                               times))
        # for start, end in multi_minute_times:
        #     scheduler.add_job(self.do_job, 'cron', hour=start.hour, minute=start.minute,
        #                       second=start.second, day_of_week='*', args=[start, end])
        logger.info(f'启动{self.name}采集{self.stock_no} {trigger}')

    def do_job(self):
        # start = datetime.now().replace(hour=start.hour, minute=start.minute, second=0)
        # end = datetime.now().replace(hour=end.hour, minute=end.minute, second=0)
        logger.info(f'采集{self.name}')
        data = self.qutation.market_snapshot(self.stock_no)
        models = list(map(lambda x: RawStock(code=x['code'], type=self.name, data=json.dumps(x), time=x['time']), data.values()))
        with get_db_context_session(False, sqlite_engine) as session:
            session.add_all(models)
            session.commit()
