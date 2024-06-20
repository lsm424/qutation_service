# encoding=utf-8
from contextlib import contextmanager
from sqlalchemy import MetaData, PrimaryKeyConstraint, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, String, DateTime, Float, BigInteger  # 区分大小写
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from common.conf import conf

base = declarative_base()


class IndexMinutePrice(base):
    __tablename__ = 't_index_minute_price'
    __table_args__ = (
        PrimaryKeyConstraint('curr_min', 'index_code'),
    )
    # 主键 primary_key | 自动增长 autoincrement | 不为空 nullable | 唯一性约束 unique
    # id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=True, unique=True)
    curr_min = Column(String(10), primary_key=True, nullable=True)
    index_code = Column(String(10), primary_key=True, nullable=True)
    last_closep = Column(Float, nullable=False, default=0)
    openp = Column(Float, nullable=False, default=0)
    highp = Column(Float, nullable=False, default=0)
    lowp = Column(Float, nullable=False, default=0)
    closep = Column(Float, nullable=False, default=0)
    min_pct_change = Column(Float, nullable=False, default=0)
    amount = Column(Float, nullable=False, default=0)
    volume = Column(Float, nullable=False, default=0)
    acc_amount = Column(Float, nullable=False, default=0)
    acc_volume = Column(Float, nullable=False, default=0)
    update_time = Column(DateTime, nullable=False, onupdate=datetime.now, default=datetime.now)


class IndexMinutePriceFull(base):
    __tablename__ = 't_index_minute_price_full'

    # 主键 primary_key | 自动增长 autoincrement | 不为空 nullable | 唯一性约束 unique
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=True, unique=True)
    trade_date = Column(String(10))
    curr_min = Column(String(10))
    index_code = Column(String(10))
    last_closep = Column(Float, nullable=False, default=0)
    openp = Column(Float, nullable=False, default=0)
    highp = Column(Float, nullable=False, default=0)
    lowp = Column(Float, nullable=False, default=0)
    closep = Column(Float, nullable=False, default=0)
    min_pct_change = Column(Float, nullable=False, default=0)
    amount = Column(Float, nullable=False, default=0)
    volume = Column(Float, nullable=False, default=0)
    acc_amount = Column(Float, nullable=False, default=0)
    acc_volume = Column(Float, nullable=False, default=0)
    update_time = Column(DateTime, nullable=False, onupdate=datetime.now, default=datetime.now)


class IndexFutureMinutePrice(base):
    __tablename__ = 't_indexfuture_minute_price'
    # id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=True, unique=True)

    curr_min = Column(String(10), primary_key=True, nullable=True)
    indexfuture_code = Column(String(20), primary_key=True, nullable=True)
    last_closep = Column(Float, nullable=False, default=0)
    last_settlep = Column(Float, nullable=False, default=0)
    openp = Column(Float, nullable=False, default=0)
    highp = Column(Float, nullable=False, default=0)
    lowp = Column(Float, nullable=False, default=0)
    closep = Column(Float, nullable=False, default=0)
    min_pct_change = Column(Float, nullable=False, default=0)
    amount = Column(Float, nullable=False, default=0)
    volume = Column(Float, nullable=False, default=0)
    acc_amount = Column(Float, nullable=False, default=0)
    acc_volume = Column(Float, nullable=False, default=0)
    holding = Column(Float, nullable=False, default=0)
    update_time = Column(DateTime, nullable=False, onupdate=datetime.now, default=datetime.now)


class IndexFutureMinutePriceFull(base):
    __tablename__ = 't_indexfuture_minute_price_full'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=True, unique=True)
    trade_date = Column(String(10))
    curr_min = Column(String(10))
    indexfuture_code = Column(String(20))
    last_closep = Column(Float, nullable=False, default=0)
    last_settlep = Column(Float, nullable=False, default=0)
    openp = Column(Float, nullable=False, default=0)
    highp = Column(Float, nullable=False, default=0)
    lowp = Column(Float, nullable=False, default=0)
    closep = Column(Float, nullable=False, default=0)
    min_pct_change = Column(Float, nullable=False, default=0)
    amount = Column(Float, nullable=False, default=0)
    volume = Column(Float, nullable=False, default=0)
    acc_amount = Column(Float, nullable=False, default=0)
    acc_volume = Column(Float, nullable=False, default=0)
    holding = Column(Float, nullable=False, default=0)
    update_time = Column(DateTime, nullable=False, onupdate=datetime.now, default=datetime.now)


sqlserver_user = conf.get('采集', 'sqlserver_user')
sqlserver_passwd = conf.get('采集', 'sqlserver_passwd')
sqlserver_host = conf.get('采集', 'sqlserver_host')
sqlserver_db = conf.get('采集', 'sqlserver_db')
engine = create_engine(f"mssql+pymssql://{sqlserver_user}:{sqlserver_passwd}@{sqlserver_host}/{sqlserver_db}?charset=utf8",
                       connect_args={'tds_version': '7.0'}, echo=False)
# Session = sessionmaker(bind=engine)
# session = Session()
# 获取元数据
metadata = MetaData(bind=engine)
index_minute_price_table = Table(IndexMinutePrice.__tablename__, metadata, autoload=True)
index_Future_minute_price_table = Table(IndexFutureMinutePrice.__tablename__, metadata, autoload=True)

# 创建数据表
base.metadata.create_all(engine, checkfirst=True)


def get_db_session():
    DbSession = sessionmaker()
    DbSession.configure(bind=engine)
    return DbSession()


@contextmanager
def get_db_context_session(transaction=False):
    session = get_db_session()

    if transaction:
        try:
            session.begin()
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        try:
            yield session
        except:
            raise
        finally:
            session.close()
