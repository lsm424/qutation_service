# encoding=utf-8
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', "--gather", help="运行采集模式", action="store_true")
    args = parser.parse_args()
    if args.gather:
        from gather.gather_stock import GaterManager
        g = GaterManager()
        g.run()
    else:
        from service.http_server import start_http_server
        from service.websocket import start_websocket_server
        start_http_server()
        start_websocket_server()
