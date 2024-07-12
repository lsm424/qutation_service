# encoding=utf-8
from functools import reduce
from itertools import groupby
import random
import time
from datetime import datetime, timedelta
from box import Box
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

# 创建一个后台调度器
scheduler = BackgroundScheduler()
scheduler.start()

stock_calendar = get_calendar('XSHG')


class Collector:

    def __init__(self, name, stock_no, triggers: list[CronTrigger]):
        self.name = name
        self.stock_no = stock_no
        self.qutation = Sina()
        for trigger in triggers:
            scheduler.add_job(self.do_job, trigger)
        logger.info(f'启动{self.name}采集{self.stock_no} {triggers}')

    def do_job(self):
        logger.info(f'采集{self.name}')
        data = self.qutation.market_snapshot(self.stock_no)
        if not data:
            return
        today = datetime.now().strftime('%Y-%m-%d')
        models = list(map(lambda x: RawStock(code=x['code'], type=self.name, data=json.dumps(x),
                      time=x['time']), filter(lambda x: x['now'] and x['time'].startswith(today), data.values())))
        if not models:
            return
        with get_db_context_session(False, sqlite_engine) as session:
            session.add_all(models)
            session.commit()


class GatherManager:
    def __init__(self, debug=False) -> None:
        delete_time = '15:02:00'.split(':')
        scheduler.add_job(self.migrate_table, 'cron', hour=int(delete_time[0]), minute=int(delete_time[1]),
                          second=int(delete_time[2]), day_of_week='*', args=[IndexMinutePrice])
        scheduler.add_job(self.migrate_table, 'cron', hour=int(delete_time[0]), minute=int(delete_time[1]),
                          second=int(delete_time[2]), day_of_week='*', args=[IndexFutureMinutePrice])
        scheduler.add_job(self.dayli_init, 'cron', hour=0, minute=1, second=0, day_of_week='*', args=[])

        self.stock_no = conf.get('采集', '指数').split(',')
        self.stock_name = {x: x[2:] + '.' + x[:2].upper() for x in self.stock_no}
        triggers = [CronTrigger(hour='10,13,14', minute='*', second="*/3"),
                    CronTrigger(hour='15', minute='0', second="*/3"),
                    CronTrigger(hour='11', minute='0-30', second="*/3"),
                    CronTrigger(hour='9', minute='24-59', second="*/3")]
        if debug:
            triggers.append(CronTrigger(hour='*', minute='*', second="*/3"))
        self.index_collector = Collector('指数', self.stock_no, triggers)
        stock_analysis_time = delta('09:26', '09:26') + delta('09:31', '11:31') + delta('13:01', '14:58') + delta('15:01', '15:01')
        self.last_stock = {x.code: x for x in self._init_last_raw_stock_by_targetime(self.stock_no) if x}

        for idx, analysis_time in enumerate(stock_analysis_time):
            scheduler.add_job(self.analysis_stock_job, 'cron', hour=analysis_time.hour, minute=analysis_time.minute,
                              second=9, day_of_week='*', args=[analysis_time, '指数', idx])

        self.future_no = conf.get('采集', '期货').split(',')
        self.future_name = {x: x.split('_')[-1] + '.CFE' for x in self.future_no}
        triggers = [CronTrigger(hour='10,13,14', minute='*', second="*/3"),
                    CronTrigger(hour='15', minute='0', second="*/3"),
                    CronTrigger(hour='11', minute='0-30', second="*/3"),
                    CronTrigger(hour='9', minute='28-59', second="*/3")]
        if debug:
            triggers.append(CronTrigger(hour='*', minute='*', second="*/3"))
        self.future_collector = Collector('期货', self.future_no, triggers)
        future_analysis_time = delta('09:30', '11:31') + delta('13:01', '15:01')
        self.last_stock.update({x.code: x for x in self._init_last_raw_stock_by_targetime(self.future_no) if x})
        self._init_last_future_closep()

        for idx, analysis_time in enumerate(future_analysis_time):
            scheduler.add_job(self.analysis_stock_job, 'cron', hour=analysis_time.hour, minute=analysis_time.minute,
                              second=9, day_of_week='*', args=[analysis_time, '期货', idx])
        # self.analysis_stock_job(datetime.now(), '期货')

    def _init_last_future_closep(self):
        with get_db_context_session(False) as session:
            models = session.query(IndexFutureMinutePriceFull.indexfuture_code, func.max(IndexFutureMinutePriceFull.id)).\
                filter(IndexFutureMinutePriceFull.indexfuture_code.in_(list(self.future_name.values()))
                       ).group_by(IndexFutureMinutePriceFull.indexfuture_code)
            ids = list(map(lambda x: x[1], models))
            models = session.query(IndexFutureMinutePriceFull).filter(IndexFutureMinutePriceFull.id.in_(ids)).all()
            self.last_future_closep = {x.indexfuture_code: x.closep for x in models}
            logger.info(f'初始化last_stock：{self.last_stock}，期货昨收closep：{self.last_future_closep}, ids:{ids}')

    def analysis_stock_job(self, target_time, stock_type, idx):
        today = datetime.now().date()
        targe_time = datetime.now().replace(hour=target_time.hour, minute=target_time.minute, second=0)
        targe_time_str = targe_time.strftime('%Y-%m-%d %H:%M:%S')

        if not stock_calendar.is_session(targe_time.strftime('%Y-%m-%d')):
            logger.warning(f'非交易日')
            return

        curr_min = targe_time - timedelta(minutes=1)
        curr_min_str = curr_min.strftime('%Y-%m-%d %H:%M:%S')

        def _run(stock_no):
            sqlit_stock_no = stock_no.split('_')[-1]
            if idx != 0:
                end = self._get_recent_by_target(sqlit_stock_no, targe_time_str)
            else:  # 第一条用开盘数据
                with get_db_context_session(False, sqlite_engine) as session:
                    end = session.query(RawStock).filter(RawStock.code == sqlit_stock_no, RawStock.create_time >=
                                                         today).order_by(RawStock.create_time.asc()).first()
            if not end:
                logger.error(f'{stock_no} 没有找到数据，目标时间 {targe_time_str}, idx: {idx}')
                return
            # 查询近分钟数据
            with get_db_context_session(False, sqlite_engine) as session:
                ret = session.query(RawStock).filter(RawStock.code == sqlit_stock_no, RawStock.id <= end.id, RawStock.create_time >= today)
                if stock_no in self.last_stock:
                    ret = ret.filter(RawStock.id >= self.last_stock[stock_no].id)
                all_data = ret.order_by(RawStock.id.asc()).all()

            # 计算表字段
            if len(all_data) > 0:
                start = Box(all_data[0].to_dict())
                start.data = Box(json.loads(start.data))
                nows = list(map(lambda x: json.loads(x.data)['now'], all_data))
                high, low = (max(nows), min(nows)) if idx != 0 else (end.data.now, end.data.now)
                volume = (end.data.volume - start.data.volume) if idx != 0 else end.data.volume
                min_pct_change = ((end.data.now - start.data.now) / start.data.now) if idx != 0 else end.data.now / float(end.data.close)
            elif len(all_data) == 1:
                high, low, volume, min_pct_change = (0, 0, 0, 0) if idx != 0 else (
                    end.data.now, end.data.now, end.data.volume, end.data.now / float(end.data.close))

            self.last_stock[stock_no] = end
            # 构造分钟记录表记录
            logger.info(f'{stock_no} 完成分析 {curr_min_str}, 开时间：{start.time}/{start.id} 收时间：{end.time}/{end.id}, high: {high}, low: {low}, idx: {idx}, len(all_data): {len(all_data)}')
            if stock_type == '指数':
                amount = 0 if len(all_data) == 1 else end.data.turn_over - start.data.turn_over
                return IndexMinutePrice(curr_min=curr_min.strftime('%H%M'), index_code=self.stock_name[stock_no], last_closep=float(end.data.close),
                                        openp=start.data.now, highp=high, lowp=low,  closep=end.data.now,
                                        volume=volume, amount=amount, min_pct_change=min_pct_change,
                                        acc_volume=end.data.volume, acc_amount=end.data.turn_over)
            elif stock_type == '期货':
                return IndexFutureMinutePrice(
                    curr_min=curr_min.strftime('%H%M'), indexfuture_code=self.future_name[stock_no],
                    last_settlep=end.data.last_settlep, last_closep=end.data.last_closep,
                    openp=start.data.now, highp=high, lowp=low, closep=end.data.now,
                    volume=volume, holding=end.data.holding, min_pct_change=min_pct_change, acc_volume=end.data.volume)

        stock_no = self.stock_no if stock_type == '指数' else self.future_no
        executor = ThreadPoolExecutor(max_workers=len(stock_no))
        r = list(map(lambda x: executor.submit(_run, x), stock_no))
        r, _ = wait(r, return_when=ALL_COMPLETED)
        r = list(map(lambda x: x.result(), r))
        with get_db_context_session(False) as session:
            session.add_all(r)
            session.commit()

    def dayli_init(self):
        logger.warning(f'delete table IndexMinutePrice and IndexFutureMinutePrice')
        with get_db_context_session(False) as session:
            session.query(IndexMinutePrice).delete()
            session.query(IndexFutureMinutePrice).delete()
            session.commit()

        now = datetime.today()
        with get_db_context_session(False, engine=sqlite_engine) as session:
            session.query(RawStock).filter(RawStock.create_time < (now - timedelta(days=3))).delete()
            session.commit()

        self.last_stock = {}
        self._init_last_future_closep()

    def migrate_table(self, table):
        now = datetime.today()
        today = now.strftime('%Y%m%d')
        if not stock_calendar.is_session(today):
            logger.warning(f'非交易日，无需迁移')
            return

        now = datetime(year=now.year, month=now.month, day=now.day)
        with get_db_context_session(False) as session:
            models = session.query(table).all()
            logger.warning(f'migrate table {table.__tablename__}, {len(models)}条')
            models = list(map(lambda x: {**x.to_dict(), **{"trade_date": today}}, models))
            if table.__tablename__ == 't_index_minute_price':
                models = list(map(lambda x: IndexMinutePriceFull(**x), models))
                session.add_all(models)
            elif table.__tablename__ == 't_indexfuture_minute_price':
                models = list(map(lambda x: IndexFutureMinutePriceFull(**x), models))
                session.add_all(models)
            session.commit()

    def _init_last_raw_stock_by_targetime(self, stock_no):
        now = datetime.now()
        if now.hour < 9 or (now.hour == 9 and now.minute < 24):
            return []

        target_time = now.replace(second=0).strftime('%Y-%m-%d %H:%M:%S')
        stock_no = list(map(lambda x: self._get_recent_by_target(x, target_time), stock_no))
        return stock_no

    # 在股票代码stock_no的数据中，找到跟target_time最接近的数据

    def _get_recent_by_target(self, stock_no, target_time):
        with get_db_context_session(False, sqlite_engine) as session:
            ret = session.query(RawStock).filter(RawStock.code == stock_no).order_by(
                func.abs(func.strftime('%s', RawStock.create_time) - func.strftime('%s', target_time))).first()
            if ret:
                ret = Box(ret.to_dict())
                ret.data = Box(json.loads(ret.data))

            return ret

    def run(self):
        while True:
            time.sleep(100)