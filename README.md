## 股票行情推送websocket服务
本项目以websocket方式对外提供股票行情的推送服务，支持行情订阅和取消订阅

## 设计简介
- 行情数据来源：新浪、腾讯api。对应目录qutaion_api的实现
- websocket服务：基于autobahn库实现websocket服务，对外提供订阅和取消订阅接口。<br/>
  生产者：通过全局的定时任务周期统一拉取所有订阅的行情，更新全局行情数据；<br/>
  消费者：各个websocket连接周期推送订阅的行情数据；<br/>
  对应目录service实现
- http服务：基于flask库提供http接口，目前只有统计相关查询接口

- 订阅协议：<br/>
订阅所有股票：```{"subscribe": []}``` <br/>
订阅000001,000002：```{"subscribe": ["000001", "000002"]}``` <br/>
取消订阅：```{"unsubscribe": []}``` <br/>


## 启动说明
#### 1、安装依赖
```pip install -r requirements.txt```

#### 2、配置说明
配置文件路径：common/config.ini
```
[股票]
# 股票代码列表，当订阅所有股票代码时，即从如下指定的股票代码获取行情
stock_code_list=000001,000002
[新浪]
# 新浪api每次调用拉取行情时，支持的最多股票代码数量。注：太大会影响拉不到数据
batch_size=800
[腾讯]
# 腾讯api每次调用拉取行情时，支持的最多股票代码数量。注：太大会影响拉不到数据
batch_size=800
[websocket推送]
# 更新股票行情时间间隔，单位秒
update_interval=1
# 推送股票行情时间间隔，单位秒
push_interval=3
# 服务端口
port=9000
# 推送间隔误差时间，单位秒
push_interval_torrlencance=0.5
[http服务]
port=80
ip=0.0.0.0
```

#### 3、启动服务
```python main.py```<br/>
启动后的打印如下：
```
2024-02-15 21:43:54.304 | INFO     | service.websocket:update_qutation_interval:104 - 目前没有订阅
2024-02-15 21:43:54.305 | INFO     | service.websocket:__init__:98 - 启动websocket服务
2024-02-15 21:43:55.304 | INFO     | service.websocket:update_qutation_interval:104 - 目前没有订阅
2024-02-15 21:43:56.305 | INFO     | service.websocket:update_qutation_interval:104 - 目前没有订阅
2024-02-15 21:44:33.779 | INFO     | qutation_api.base:market_snapshot:63 - 完成行情数据获取5122条，总耗时：0.47124218940734863，网络耗时：0.35355424880981445，数据组装耗时：0.11769390106201172
2024-02-15 21:44:34.209 | INFO     | service.websocket:send_qutation_interval:41 - 完成推送到 tcp4:127.0.0.1:57475
```

#### 4、客户端实现参考
```python websocket_client_example.py```<br/>
启动后打印如下：
```
2024-02-15 19:17:18+0800 [-] Log opened.
2024-02-15 19:17:18+0800 [-] Starting factory <autobahn.twisted.websocket.WebSocketClientFactory object at 0x7fab16e07a00>
2024-02-15 19:17:18+0800 [-] client open
2024-02-15 19:17:18+0800 [-] Text message received: {"code": 0, "message": ""}
2024-02-15 19:17:22+0800 [-] Text message received: {"sz002138": {"name": "\u987a\u7edc\u7535\u5b50", "open": 26.64, "close": 26.63, "now": 26.04, "high
2024-02-15 19:17:27+0800 [-] Text message received: {"sz159907": {"name": "2000ETF", "open": 1.132, "close": 1.119, "now": 1.195, "high": 1.209, "low": 
```

#### 5、查看统计数据
- 查看全量推间隔分布数据图url：http://ip:port/statistic/interval
- 查看2024-02-23日到2024-02-24日之间的推间隔分布数据图url：http://ip:port/statistic/interval?start=2024-02-23&end=2024-02-24