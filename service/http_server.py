import threading

from flask import Flask, send_file, request

from common.conf import conf
from statistic.statistic import statistic_manager

app = Flask(__name__)


def start_http_server():
    t = threading.Thread(target=app.run, args=(conf.get('http服务', 'ip'), conf.getint('http服务', 'port')))
    t.setDaemon(True)
    t.start()


@app.route('/statistic/interval')
def get_interval():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    buf = statistic_manager.show_push_interval_image(start_date, end_date)
    return send_file(buf, mimetype='image/svg+xml')