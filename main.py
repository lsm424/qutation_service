# encoding=utf-8
from service.http_server import start_http_server
from service.websocket import start_websocket_server

if __name__ == '__main__':
    start_http_server()
    start_websocket_server()