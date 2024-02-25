# encoding=utf-8
import json
import threading
import time
from functools import reduce

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

from twisted.internet import task, reactor

from common.conf import conf
from common.log import logger
from qutation_api.sina import Sina
from statistic.model import QutationLogModel
from statistic.statistic import statistic_manager


class WebSocketServer(WebSocketServerProtocol):
    CMD_SUBSCRIBE = 'subscribe'         # 订阅命令
    CMD_UNSUBSCRIBE = 'unsubscribe'     # 取消订阅

    # 订阅返回码
    RET_CODE_SUCCSSS = 0        # 订阅成功
    RET_CODD_NOT_JSON = -1      # 订阅失败，订阅请求不是json
    RET_CODE_ERROR_CMD = -2     # 订阅失败，订阅请求的json中未包含key subscribe
    RET_CODE_ERROR_VALUE = -3   # 订阅失败，订阅请求的json中的value不是list[str]

    lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stock_code = None
        self.qutation = None
        self.send_message_loop = task.LoopingCall(self.send_qutation_interval, "Hello, clients!")
        self.interval = conf.getint('websocket推送', 'push_interval')

    def send_qutation_interval(self, message):
        data = {}
        if self.qutation:
            data = self.qutation
        self.sendMessage(json.dumps(data).encode('utf-8'), isBinary=False)
        statistic_manager.push_qutation_log(self.client_name, self.client_id, QutationLogModel.OPR_PUSH, data)
        logger.info(f'完成推送到 {self.peer}')

    def _parse_payload(self, raw_payload):
        try:
            payload = json.loads(raw_payload)
        except BaseException as e:
            logger.error(f'websocket收到消息格式错误，非json: {raw_payload}')
            return self.RET_CODD_NOT_JSON, '消息非json'

        if not isinstance(payload, dict):
            return self.RET_CODD_NOT_JSON, '消息非dict'
        elif self.CMD_SUBSCRIBE in payload:
            stock_code = payload[self.CMD_SUBSCRIBE]
            if not isinstance(stock_code, list) or any(map(lambda x: not isinstance(x, str), stock_code)):
                logger.error(f'websocket收到消息的json key {self.CMD_SUBSCRIBE}\' 对应的value不是list[str], json: {payload}')
                return self.RET_CODE_ERROR_VALUE, 'value类型非list[str]',
            self.stock_code = stock_code
            with WebSocketServer.lock:
                self.factory.clients.add(self)
            if not self.send_message_loop.running:
                self.send_message_loop.start(self.interval, now=False)
            logger.info(f'{self.peer} 开启订阅 {payload}')
            statistic_manager.push_qutation_log(self.client_name, self.client_id, QutationLogModel.OPR_SUBSCRIBE, raw_payload)
        elif self.CMD_UNSUBSCRIBE in payload:
            self.stock_code = None
            if self.send_message_loop.running:
                self.send_message_loop.stop()
            logger.info(f'{self.peer} 取消订阅')
            statistic_manager.push_qutation_log(self.client_name, self.client_id, QutationLogModel.OPR_UNSUBSCRIBE)
        else:
            logger.error(f'websocket收到消息的cmd不支持, json: {payload}')
            return self.RET_CODE_ERROR_CMD, '不支持的cmd'
        return self.RET_CODE_SUCCSSS, ''

    def onConnect(self, request):
        logger.info(f"客户端接入： {request.peer}")
        self.client_id = f'{request.peer}_{int(time.time() * 1000)}'
        self.client_name = request.peer

    def onOpen(self):
        pass

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode('utf8')
        code, msg = self._parse_payload(payload)
        self.sendMessage(json.dumps({'code': code, 'message': msg}).encode('utf-8'))

    def onClose(self, wasClean, code, reason):
        logger.info(f"WebSocket connection closed: {reason}")
        statistic_manager.push_qutation_log(self.client_name, self.client_id, QutationLogModel.OPR_OFFLINE)
        with WebSocketServer.lock:
            try:
                self.factory.clients.remove(self)
            except BaseException as e:
                pass
        if self.send_message_loop.running:
            self.send_message_loop.stop()


class QutationServerFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clients = set()
        self.qutation = Sina()
        interval = conf.getint('websocket推送', 'update_interval')
        self.send_message_loop = task.LoopingCall(self.update_qutation_interval, "Hello, clients!")
        self.send_message_loop.start(interval)
        logger.info(f'启动websocket服务')

    def update_qutation_interval(self, message):
        with WebSocketServer.lock:
            stock_code_list = list(filter(lambda x: x is not None, map(lambda x: x.stock_code, self.clients)))
            if not stock_code_list:
                logger.info(f'目前没有订阅')
                return

        # 根据股票代码拉取股票信息
        stock_code = list(set(reduce(lambda x, y: x + y, stock_code_list)))
        try:
            qutation_dict = self.qutation.market_snapshot(stock_code)
        except BaseException as e:
            logger.error(f'获取行情失败：{e}')
            return

        # 分发推送
        with WebSocketServer.lock:
            for c in self.clients:
                qutation = qutation_dict
                if c.stock_code:
                    qutation = {k: v for k, v in qutation_dict.items() if k in c.stock_code}
                c.qutation = qutation


def start_websocket_server():
    factory = QutationServerFactory()
    factory.protocol = WebSocketServer
    reactor.listenTCP(conf.getint('websocket推送', 'port'), factory)
    reactor.run()
