import threading

from flask import Flask, send_file, request

from common.conf import conf
from common.log import logger
from statistic.statistic import statistic_manager
from gather.gather_manager import Collector

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


@app.route('/collector/set_flag')
def set_flag():
    try:
        flag = eval(request.args.get('flag'))
    except BaseException as e:
        logger.error(f'set_flag error:{e}， param: {request.args}')
        return '设置失败'

    Collector.set_run_gather(flag)
    return '设置成功'
