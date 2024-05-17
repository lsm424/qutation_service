from configparser import ConfigParser
import os

conf = ConfigParser()
cur_path = os.getcwd()
root = os.path.join(cur_path[: cur_path.find('qutation_service')], 'qutation_service')
__file = os.path.join(root, 'common', 'config.ini')
conf.read(__file, encoding='utf-8')


def update_conf(section, key, value):
    conf[section] = {key: value}
    with open(__file, 'w') as f:
        conf.write(f)
