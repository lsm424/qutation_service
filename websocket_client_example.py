import json

from autobahn.twisted import WebSocketClientProtocol


class MyClientProtocol(WebSocketClientProtocol):

    def onOpen(self):
        print('client open')
        self.sendMessage(json.dumps({'subscribe': []}).encode('utf-8'))

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')[:100]))


import sys

from twisted.python import log
from twisted.internet import reactor

log.startLogging(sys.stdout)

from autobahn.twisted.websocket import WebSocketClientFactory

factory = WebSocketClientFactory()
factory.protocol = MyClientProtocol

reactor.connectTCP("127.0.0.1", 9000, factory)
reactor.run()
