from configparser import ConfigParser

conf = ConfigParser()
__file = './common/config.ini'
conf.read(__file)


def update_conf(section, key, value):
    conf[section] = {key: value}
    with open(__file, 'w') as f:
        conf.write(f)
