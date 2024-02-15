# encoding=utf-8
from common.conf import conf
from service.websocket import WebSocketServer, QutationServerFactory
from twisted.internet import reactor

if __name__ == '__main__':
    factory = QutationServerFactory()
    factory.protocol = WebSocketServer
    reactor.listenTCP(conf.getint('websocket推送', 'port'), factory)
    reactor.run()
