from configparser import ConfigParser

conf = ConfigParser()
__file = './common/config.ini'
conf.read(__file, encoding='utf-8')


def update_conf(section, key, value):
    conf[section] = {key: value}
    with open(__file, 'w') as f:
        conf.write(f)
