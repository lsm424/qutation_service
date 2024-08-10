import csv
from datetime import datetime
import threading
import os
from common.utils import send_mail
from common.log import logger


class ErrRecord:
    def __init__(self) -> None:
        self.err_file = 'err.csv'
        self.headers = ['时间', '错误信息']
        self.lock = threading.Lock()
        if not os.path.exists(self.err_file):
            open(self.err_file, 'w', newline='').close()

        with open(self.err_file) as f:
            rows = list(csv.reader(f))
        if not rows:
            with open(self.err_file, 'w', newline='')as f:
                f_csv = csv.DictWriter(f, self.headers)
                f_csv.writeheader()
        logger.info(f'创建错误记录文件 {self.err_file}')

    def record_error(self, err: str):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.lock:
            with open(self.err_file, 'a', newline='')as f:
                f_csv = csv.DictWriter(f, self.headers)
                f_csv.writerow({'时间': now, '错误信息': err})
        send_mail(err)


err_recorder = ErrRecord()
