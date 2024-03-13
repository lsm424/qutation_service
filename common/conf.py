from configparser import ConfigParser
import os

conf = ConfigParser()
cur_path = os.getcwd()
root = cur_path[: cur_path.find('quotation_service')] + '/quotation_service'
__file = os.path.join(os.path.relpath(root, start=cur_path), './common/config.ini')
conf.read(__file)


def update_conf(section, key, value):
    conf[section] = {key: value}
    with open(__file, 'w') as f:
        conf.write(f)
