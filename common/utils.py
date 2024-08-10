# encoding=utf-8
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.text import MIMEText
import smtplib
from common.log import logger
from common.conf import conf
import yagmail


def delta(start, end):
    start = datetime.strptime(start, '%H:%M')
    end = datetime.strptime(end, '%H:%M')
    delta_mins = int((end - start).seconds / 60) + 1
    delta = list(map(lambda x: start + timedelta(minutes=x), range(delta_mins)))
    # delta = {(t - timedelta(seconds=2)).strftime('%H:%M:%S'): t for t in delta}  # key：启动任务时间，提前几秒； value：采集的目标时间
    return delta


def send_mail(msg, receivers: list = conf.get('告警', '邮件接收人列表').split(','), subject='股票采集错误通知'):
    try:
        yag = yagmail.SMTP(user=conf.get('告警', '发件人用户名'), password=conf.get('告警', '发件人密码'), host=conf.get('告警', '发件人邮箱服务器'))

        yag.send(to=receivers, subject=subject, contents=msg)
        logger.info("邮件发送成功")
    except smtplib.SMTPException as e:
        logger.error(f"Error: 无法发送邮件, {e}")
