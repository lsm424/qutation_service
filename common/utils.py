# encoding=utf-8
from datetime import datetime, timedelta


def delta(start, end):
    start = datetime.strptime(start, '%H:%M')
    end = datetime.strptime(end, '%H:%M')
    delta_mins = int((end - start).seconds / 60) + 1
    delta = list(map(lambda x: start + timedelta(minutes=x), range(delta_mins)))
    # delta = {(t - timedelta(seconds=2)).strftime('%H:%M:%S'): t for t in delta}  # key：启动任务时间，提前几秒； value：采集的目标时间
    return delta
