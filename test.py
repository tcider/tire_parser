import configparser
import os
import logging

# Reading global constants from config.ini.tmpl
CONFIG_FILE = "config.ini.tmpl"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        config_content = '[config]\n' + f.read()
    config = configparser.ConfigParser()
    config.read_string(config_content)
    DB_SERVER_FROM_CONFIG = config.get('config', 'DB_SERVER')
    DB_NAME_FROM_CONFIG = config.get('config', 'DB_NAME')
    DB_USER_FROM_CONFIG = config.get('config', 'DB_USER')
    DB_PASSWORD_FROM_CONFIG = config.get('config', 'DB_PASSWORD')
    LOGIN_FROM_CONFIG = config.get('config', 'LOGIN')
    PASSWORD_FROM_CONFIG = config.get('config', 'PASSWORD')
    MIN_PARSE_PAUSE = config.get('config', 'MIN_PARSE_PAUSE')
    MAX_PARSE_PAUSE = config.get('config', 'MAX_PARSE_PAUSE')
    CURRENCY_RATE = config.get('config', 'CURRENCY_RATE')
    UPDATE_NEW_PRICES = config.get('config', 'UPDATE_NEW_PRICES')
else:
    pass #FIXME What if config file not exists

from tire_parser import TireParser


_parser = TireParser()


