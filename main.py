# encoding=utf-8
import argparse
from service.http_server import start_http_server
from statistic.statistic import statistic_manager

# from gather.model import *


# def test(stock_no, target_time):
#     from sqlalchemy import func
#     with get_db_context_session(False, sqlite_engine) as session:
#         ret = session.query(RawStock).filter(RawStock.type == '指数', RawStock.code == stock_no).order_by(
#             func.abs(func.strftime('%s', RawStock.create_time) - func.strftime('%s', target_time))).first()
#         return ret


if __name__ == '__main__':
    # test('sz000905', '2024-06-27 11:36:48')

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', "--gather", help="运行采集模式", action="store_true")
    args = parser.parse_args()
    start_http_server()
    if args.gather:
        from gather.gather_manager import GatherManager
        g = GatherManager()
        g.run()
    else:
        from service.websocket import start_websocket_server
        start_websocket_server()
        statistic_manager.start()
