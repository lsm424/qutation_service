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

stock_calendar = get_calendar('XSHG')

scheduler = BackgroundScheduler()
scheduler.start()


class Gather:
    def __init__(self, stock_no, time_info: list[datetime], save_stock, name):
        self.name = name
        self.stock_no = stock_no
        self.get_timestamp = time_info
        self.save_stock = save_stock
        self.qutation = [Sina(), Tencent()]
        for idx, target_time in enumerate(self.get_timestamp):
            start_time = target_time - timedelta(seconds=2)
            scheduler.add_job(self.do_job, 'cron', hour=start_time.hour, minute=start_time.minute,
                              second=start_time.second, day_of_week='*', args=[target_time, idx])
        logger.info(f'启动{name}采集：{self.stock_no}，时间点：{sorted(map(lambda x: x.strftime("%H:%M:%S"), self.get_timestamp))}')

    def do_job(self, date_time: datetime, idx):
        targe_time = datetime.now().replace(hour=date_time.hour, minute=date_time.minute, second=0)
        targe_time_str = targe_time.strftime('%Y-%m-%d %H:%M:%S')
        if not stock_calendar.is_session(targe_time_str.split(' ')[0]):
            logger.warning(f'第{idx}轮采集{self.name}退出，非交易日')
            return
        logger.info(f'第{idx}轮采集{self.name}开始，目标时间：{targe_time}')

        def _run(i):
            ret = []
            start = time.time()
            while time.time() - start < 10:
                time.sleep(random.randint(40, 100) / 1000)
                for qutation in self.qutation:
                    data = list(qutation.market_snapshot(self.stock_no).values())
                    if data:
                        ret += data
                        break
                else:
                    continue

                if all(map(lambda x: x['time'] >= targe_time_str, data)):
                    if idx == 0 and any(map(lambda x: not x['open'])):
                        logger.info(f'{i} 存在未开市的stock_no，继续刷..')
                        continue
                    logger.info(f'{i} 已采集到时间点 {targe_time_str} 的{self.name}')
                    break
            else:
                logger.warning(f'{i} 未能全量采集到时间点{self.name} {targe_time_str}')
            return ret

        executor = ThreadPoolExecutor(max_workers=5)
        r = list(map(lambda x: executor.submit(_run, x), range(2)))
        r, _ = wait(r, return_when=ALL_COMPLETED)
        r = reduce(lambda x, y: x + y, map(lambda x: x.result(), r))
        if not r:
            logger.error(f'时间点{targe_time_str}的{self.name}数据获取失败')
            return

        r = groupby(sorted(r, key=lambda x: x['code']), key=lambda x: x['code'])
        stocks = []
        for code, stock_list in r:
            stock_list = sorted(stock_list, key=lambda x: abs(datetime.strptime(x['time'], '%Y-%m-%d %H:%M:%S').timestamp() - targe_time.timestamp()))
            stocks.append(stock_list[0])
        self.save_stock.save(stocks)


class IndexSave:
    def __init__(self, init_time) -> None:
        self.stocks = conf.get('采集', '指数').split(',')
        self._init()
        init_time = init_time.split(':')
        scheduler.add_job(self._init, 'cron', hour=int(init_time[0]), minute=int(init_time[1]), second=int(init_time[2]), day_of_week='*')

    def _init(self):
        with get_db_context_session(False) as session:
            models = session.query(IndexMinutePriceFull.index_code, func.max(IndexMinutePriceFull.id)).\
                filter(IndexMinutePriceFull.index_code.in_(self.stocks)).group_by(IndexMinutePriceFull.index_code)
            ids = list(map(lambda x: x[1], models))
            models = session.query(IndexMinutePriceFull).filter(IndexMinutePriceFull.id.in_(ids)).all()
        self.acc_amount = {x.index_code: x.acc_amount for x in models}
        self.acc_volume = {x.index_code: x.acc_volume for x in models}
        self.closep = {x.index_code: x.closep for x in models}
        logger.info(f'初始化股票acc_amout：{self.acc_amount}，acc_volume：{self.acc_volume}，closep：{self.closep}, ids: {ids}')

    def save(self, stocks: list):
        stock_models = list(map(lambda x: IndexMinutePrice(curr_min=x['time'].split(' ')[-1], index_code=x['code']+str(time.time())[-4:], last_closep=float(x['close']),
                                                           openp=float(x['open']), highp=float(x['high']), lowp=float(x['low']),
                                                           volume=x['volume'], amount=x['turn_over'], closep=float(x['now']),
                                                           min_pct_change=1 if not self.closep.get(x['code'], None) else (
                                                               (float(x['now']) - self.closep[x['code']]) / self.closep[x['code']]),
                                                           acc_volume=x['volume'] + self.acc_volume.get(x['code'], 0),
                                                           acc_amount=x['turn_over'] + self.acc_amount.get(x['code'], 0)), stocks))
        with get_db_context_session(False) as session:
            session.add_all(stock_models)
            session.commit()

        for stock in stocks:
            self.acc_amount[stock['code']] = self.acc_amount.get(stock['code'], 0) + stock['turn_over']
            self.acc_volume[stock['code']] = self.acc_volume.get(stock['code'], 0) + stock['volume']
            self.closep[stock['code']] = stock['now']


# 期货数据保存
class FutureSave:
    def __init__(self, init_time) -> None:
        self.stocks = list(map(lambda x: x.split('_')[-1], conf.get('采集', '期货').split(',')))
        self._init()
        init_time = init_time.split(':')
        scheduler.add_job(self._init, 'cron', hour=int(init_time[0]), minute=int(init_time[1]), second=int(init_time[2]), day_of_week='*')

    def _init(self):
        with get_db_context_session(False) as session:
            models = session.query(IndexFutureMinutePriceFull.indexfuture_code, func.max(IndexFutureMinutePriceFull.id)).\
                filter(IndexFutureMinutePriceFull.indexfuture_code.in_(self.stocks)).group_by(IndexFutureMinutePriceFull.indexfuture_code)
            ids = list(map(lambda x: x[1], models))
            models = session.query(IndexFutureMinutePriceFull).filter(IndexFutureMinutePriceFull.id.in_(ids)).all()
            self.acc_amount = {x.indexfuture_code: x.acc_amount for x in models}
            self.acc_volume = {x.indexfuture_code: x.acc_volume for x in models}
            self.closep = {x.indexfuture_code: x.closep for x in models}
            self.last_closep = {x.indexfuture_code: x.closep for x in models}
            logger.info(f'初始化期货acc_amout：{self.acc_amount}，acc_volume：{self.acc_volume}，closep：{self.closep}, ids:{ids}')

    def save(self, stocks: list):
        stock_models = list(map(lambda x: IndexFutureMinutePrice(
            curr_min=x['time'].split(' ')[-1],
            indexfuture_code=x['code'],
            last_settlep=float(x['last_settlep']),
            last_closep=self.last_closep.get(x['code'], 0),
            openp=float(x['open']),
            highp=float(x['high']),
            lowp=float(x['low']),
            volume=x['volume'],
            holding=x['holding'],
            closep=float(x['now']),
            min_pct_change=1 if not self.closep.get(x['code'], None) else ((float(x['now']) - self.closep[x['code']]) / self.closep[x['code']]),
            acc_volume=x['volume'] + self.acc_volume.get(x['code'], 0),
            acc_amount=x.get('turn_over', 0) + self.acc_amount.get(x['code'], 0)), stocks))

        with get_db_context_session(False) as session:
            session.add_all(stock_models)
            session.commit()

        for stock in stocks:
            self.acc_amount[stock['code']] = self.acc_amount.get(stock['code'], 0) + stock.get('turn_over', 0)
            self.acc_volume[stock['code']] = self.acc_volume.get(stock['code'], 0) + stock['volume']
            self.closep[stock['code']] = stock['now']


class GaterManager:
    def __init__(self, debug=False) -> None:
        # 定时迁移到full表，并清理天表
        delete_time = '15:01:00'.split(':')
        scheduler.add_job(self.delete_migrate_table, 'cron', hour=int(delete_time[0]), minute=int(delete_time[1]),
                          second=int(delete_time[2]), day_of_week='*', args=[IndexMinutePrice])
        scheduler.add_job(self.delete_migrate_table, 'cron', hour=int(delete_time[0]), minute=int(delete_time[1]),
                          second=int(delete_time[2]), day_of_week='*', args=[IndexFutureMinutePrice])
        self.delete_migrate_table(IndexMinutePrice)
        self.delete_migrate_table(IndexFutureMinutePrice)

        # 启动指数采集
        stock_no = conf.get('采集', '指数').split(',')
        time_info = delta('09:25', '09:25') + delta('09:31', '11:30') + delta('13:01', '14:57') + delta('15:00', '15:00')
        now = datetime.now()
        if debug:
            time_info.append(now + timedelta(seconds=5))
        self.gather_index = Gather(stock_no, time_info, IndexSave(init_time='00:02:00'), '股指')

        # 启动期货采集
        stock_no = conf.get('采集', '期货').split(',')
        time_info = delta('09:29', '11:30') + delta('13:01', '15:00')
        if debug:
            time_info.append(now + timedelta(seconds=5))
        self.gather_Future = Gather(stock_no, time_info, FutureSave(init_time='00:02:00'), '期货')

    def delete_migrate_table(self, table):
        now = datetime.today()
        today = now.strftime('%Y-%m-%d')
        # if not stock_calendar.is_session(today):
        #     logger.warning(f'非交易日，无需迁移')
        #     return

        now = datetime(year=now.year, month=now.month, day=now.day)
        with get_db_context_session(False) as session:
            if today > '15:00:00':
                models = session.query(table).all()
                logger.warning(f'migrate table {table.__tablename__}, {len(models)}条')
                models = list(map(lambda x: {**x.to_dict(), **{"trade_date": today}}, models))
                if table.__tablename__ == 't_index_minute_price':
                    models = list(map(lambda x: IndexMinutePriceFull(**x), models))
                    session.add_all(models)
                elif table.__tablename__ == 't_indexfuture_minute_price':
                    models = list(map(lambda x: IndexFutureMinutePriceFull(**x), models))
                    session.add_all(models)
            logger.warning(f'delete table {table.__tablename__} < {today}')
            session.query(table).filter(table.update_time < now).delete()
            session.commit()

    def run(self):
        while True:
            time.sleep(1000)
