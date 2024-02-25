# encoding=utf-8
from peewee import SqliteDatabase, Model, CharField, IntegerField, DateTimeField, SQL, TextField, AutoField, FloatField

sqlite_db = SqliteDatabase('quotation.db')


# qutation推送日志表
class QutationLogModel(Model):
    # 操作类型枚举值
    OPR_SUBSCRIBE = 1       # 订阅
    OPR_PUSH = 2            # 推送
    OPR_UNSUBSCRIBE = 3     # 取消订阅
    OPR_OFFLINE = 4         # 下线

    # 分析状态枚举值
    ANA_SUCC = 0            # 分析成功
    ANA_ERROR_INTERVAL = 1  # 分析有问题，推送超过间隔

    id = AutoField(primary_key=True, verbose_name='自增id')
    client_name = CharField(max_length=256, verbose_name='客户端名称', null=False)
    client_id = CharField(max_length=256, verbose_name='客户端uuid', null=False)
    opr = IntegerField(default=0, verbose_name='操作类型', null=False)
    data = TextField(default='', verbose_name='操作数据', null=False)
    avg_time = FloatField(default=0.0, verbose_name='timestamp平均值', null=False)
    analysis_statue = IntegerField(default=ANA_SUCC, verbose_name='分析状态值', null=False)
    analysis_desc = CharField(default='', max_length=512, verbose_name='分析结果描述信息', null=False)
    create_time = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], verbose_name='创建时间', null=False)

    class Meta:
        database = sqlite_db
        table_name = "qutation_log"
        constraints = [SQL('UNIQUE (client_id, opr, create_time)')]
        # table_settings = ['DEFAULT CHARSET=utf8']


if not QutationLogModel.table_exists():
    QutationLogModel.create_table()