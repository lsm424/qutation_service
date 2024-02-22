# encoding=utf-8
import io
import threading

from flask import Flask, Response
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from statistic.statistic import statistic_manager

app = Flask(__name__)


def start_http_server():
    t = threading.Thread(target=app.run, args=('0.0.0.0', 80))
    t.setDaemon(True)
    t.start()


@app.route('/statistic/push_interval')
def push_interval():
    png = statistic_manager.show_push_interval_image()
    # 将 PNG 图像作为字节流返回给客户端
    return Response(png, mimetype='image/svg+xml')

