# coding=utf-8;
import csv
import os
import datetime
import sys
import time
import random
from decimal import Decimal
from typing import Union

import requests

import delivery_company
from tire_parser import TireParser, COUNTRIES
import pyodbc

import configparser
import logging


# Reading global constants from config.ini.tmpl
CONFIG_FILE = "config.ini"
LOGGING_FILE = "log.txt"


logging.basicConfig(filename=LOGGING_FILE, level=logging.INFO)


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
    logging.warning(f"Config file {CONFIG_FILE} not exists")


_parser = TireParser()


class DBItem:
    tyre2_id: None
    kod: None
    name: None
    price: None
    retail_price: None
    carrier_info: None
    in_stock: None

    def __init__(self, tire2_id, kod, name, price, retail_price, carrier_info, in_stock):
        self.tyre2_id = tire2_id
        self.kod = kod
        self.name = name
        self.price = price
        self.retail_price = retail_price
        self.carrier_info = carrier_info
        self.in_stock = in_stock


class CSVItem:
    def __init__(self):
        self.tire_id = None
        self.kod = None
        self.name = None
        self.price = None
        self.retail_price = None
        self.carrier_info = None
        self.in_stock = None
        self.transport_price_de_at_pl = None
        self.transport_price_fr_be_it = None
        self.pass_price_de_at_pl = None
        self.pass_price_fr_be_it = None
        self.first_place_price = None
        self.first_place_name = None
        self.second_place_price = None
        self.min_in_stock = None
        self.new_price = None

    def to_dict(self):
        return {
            "tire_id": self.tire_id,
            "kod": self.kod,
            "name": self.name,
            "price": self.price,
            "retail_price": self.retail_price,
            "carrier_info": self.carrier_info,
            "in_stock": self.in_stock,
            "transport_price_de_at_pl": self.transport_price_de_at_pl,
            "transport_price_fr_be_it": self.transport_price_fr_be_it,
            "pass_price_de_at_pl": self.pass_price_de_at_pl,
            "pass_price_fr_be_it": self.pass_price_fr_be_it,
            "first_place_price": self.first_place_price,
            "first_place_name": self.first_place_name,
            "second_place_price": self.second_place_price,
            "min_in_stock": self.min_in_stock,
            "new_price": self.new_price,
        }


def get_currency_rate():
    if not CURRENCY_RATE:
        resp = requests.get("http://www.cnb.cz/cs/financni_trhy/devizovy_trh/kurzy_devizoveho_trhu/denni_kurz.txt")
        with open("data/currency.txt", "w") as f:
            f.write(resp.text)
        with open("data/currency.txt", "r") as f:
            for row in f:
                if row.lower().startswith("emu|euro|1|eur|"):
                    return Decimal(row.lower().split("|")[-1].replace(",", "."))
    else:
        return CURRENCY_RATE


def fetch_tires_from_db(cursor):
    sql = "select SKz.VPrdfghu as TYRE24ID, SKz.IDS as kod, SKz.Nazev as Name, " \
          "SKz.VNakup as vazenaPrice, SKz.ProdejKc*1.02+400 as retailPrice, " \
          "SKz.VPrCarrierInfo as CarrierInfo, " \
          "SKz.StavZ as InStock " \
          "from SKz join sSklad on sSklad.ID = SKz.RefSklad where SKz.IObchod = ('1')" \
          " and ssklad.IDS = 'Pneumatiky' and VPrdfghu is not NULL and StavZ > 0"
    cursor.execute(sql)
    rows = cursor.fetchall()

    return [
        DBItem(row.TYRE24ID, row.kod, row.Name, row.vazenaPrice, row.retailPrice, row.CarrierInfo, row.InStock)
        for row in rows
    ]


def update_item_price_in_db(cursor, id: Union[str, int], new_price: Union[str, int]) -> None:
    sql = f"update SKzCn set SKzCn.ProdejC = {new_price} from SKz " \
          "join SKzCn ON SKzCn.RefAg = SKz.ID " \
          "join SkCeny on SkCeny.ID = SKzCn.RefSkCeny " \
          f"where SKz.VPrdfghu = {id} and SkCeny.IDS = 'TYRE24 FRA'"
    cursor.execute(sql)


def calculate_transport_price_de_at_pl(carrier_info):
    delivery_id = str(carrier_info)[0]
    count_of_tires_index = int(str(carrier_info)[1])

    shipping_company = delivery_company.get_delivery_company(int(delivery_id))

    return round(shipping_company.de_at_pl_one_place_delivery_cost() / get_currency_rate() / Decimal(shipping_company.count_of_tires(count_of_tires_index)), 2)


def calculate_transport_price_fr_be_it(carrier_info):
    delivery_id = str(carrier_info)[0]
    count_of_tires_index = int(str(carrier_info)[1])

    shipping_company = delivery_company.get_delivery_company(int(delivery_id))

    return round(shipping_company.fr_be_it_one_place_delivery_cost() / get_currency_rate() / Decimal(shipping_company.count_of_tires(count_of_tires_index)), 2)


def calculate_pass_price_de_at_pl(csv_item):
    return round(csv_item.price * Decimal(1.0) / get_currency_rate() + csv_item.transport_price_de_at_pl, 2)


def calculate_pass_price_fr_be_it(csv_item):
    return round(csv_item.price * Decimal(1.0) / get_currency_rate() + csv_item.transport_price_fr_be_it, 2)


def loss(csv_item: CSVItem):
    return round(Decimal(0.8) + csv_item.price * Decimal(1.0) / get_currency_rate() * Decimal(0.03), 2)


def calculate_new_price(csv_item: CSVItem, country):
    if country in ['de', 'at', 'pl']:
        pass_price = csv_item.pass_price_de_at_pl
    else:
        pass_price = csv_item.pass_price_fr_be_it

    new_price = round(Decimal(csv_item.retail_price) / get_currency_rate(), 2)

    delta = loss(csv_item)

    if csv_item.first_place_price:
        if csv_item.first_place_price >= pass_price - delta:
            if csv_item.first_place_name == '204010':
                if (csv_item.second_place_price - csv_item.first_place_price) > 0.5:
                    new_price = csv_item.second_place_price - 0.29
                else:
                    new_price = csv_item.first_place_price
            else:
                new_price = csv_item.first_place_price - 0.1
        else:
            new_price = pass_price - delta

    return round(new_price, 2)


def parse_tire_id(session, csv_item: CSVItem, country: str):
    parsed_items = _parser.parse_tire(session, csv_item.tire_id, country)

    csv_item.transport_price_de_at_pl = calculate_transport_price_de_at_pl(csv_item.carrier_info)
    csv_item.transport_price_fr_be_it = calculate_transport_price_fr_be_it(csv_item.carrier_info)
    csv_item.pass_price_de_at_pl = calculate_pass_price_de_at_pl(csv_item)
    csv_item.pass_price_fr_be_it = calculate_pass_price_fr_be_it(csv_item)
    if parsed_items:
        csv_item.first_place_price = float(parsed_items[0].priceek)
        csv_item.first_place_name = parsed_items[0].wholesalerid
        csv_item.min_in_stock = parsed_items[0].stock
        if len(parsed_items) > 1:
            csv_item.second_place_price = float(parsed_items[1].priceek)
    csv_item.new_price = calculate_new_price(csv_item, country)
    return csv_item


def write_to_csv(csv_items, args_country: str):
    date_of_file = datetime.datetime.now().strftime("%Y-%m-%d%__%h-%M")
    with open(f'data/tires__{args_country}__{date_of_file}.csv', 'w', newline='') as csvfile:
        fieldnames = [
            "tire_id",
            "kod",
            "name",
            "price",
            "retail_price",
            "carrier_info",
            "in_stock",
            "transport_price_de_at_pl",
            "transport_price_fr_be_it",
            "pass_price_de_at_pl",
            "pass_price_fr_be_it",
            "first_place_price",
            "first_place_name",
            "second_place_price",
            "min_in_stock",
            "new_price",
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        writer.writerows([item.to_dict() for item in csv_items])


if __name__ == "__main__":
    if not os.path.exists('data/'):
        os.mkdir("data")

    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + DB_SERVER_FROM_CONFIG + ';DATABASE=' + DB_NAME_FROM_CONFIG + ';UID=' + DB_USER_FROM_CONFIG + ';PWD=' + DB_PASSWORD_FROM_CONFIG)
    cursor = conn.cursor()

    # print(f'Started at {datetime.datetime.now()}')
    logging.info(f'Started at {datetime.datetime.now()}')
    CURRENCY_RATE = get_currency_rate()
    # print(f'CURRENCY RATE {CURRENCY_RATE}')
    logging.info(f'CURRENCY RATE {CURRENCY_RATE}')

    db_tires = fetch_tires_from_db(cursor)[:50]

    args_country = sys.argv[1]

    if args_country not in COUNTRIES:
        # print("Invalid country name. Use on of [" + ", ".join(COUNTRIES.keys()) + "]")
        logging.error("Invalid country name. Use on of [" + ", ".join(COUNTRIES.keys()) + "]")
        sys.exit(-1)

    total_count = len(db_tires)

    csv_items = []
    session = _parser.login()

    for i, db_tire in enumerate(db_tires):
        csv_item = CSVItem()
        csv_item.tire_id = db_tire.tyre2_id
        csv_item.kod = db_tire.kod
        csv_item.name = db_tire.name
        csv_item.price = db_tire.price
        csv_item.carrier_info = db_tire.carrier_info
        csv_item.retail_price = db_tire.retail_price
        csv_item.in_stock = db_tire.in_stock

        random_pause = random.randrange(MIN_PARSE_PAUSE, MAX_PARSE_PAUSE)
        # print(f'Process tire {csv_item.tire_id}. {i} of {total_count}. Paused: {random_pause} sec.')
        # страна, tyre24 - id, kod, name, очередность, пауза
        logging.info(f'{args_country}, {csv_item.tire_id}, {csv_item.kod}, {csv_item.name}, {i} of {total_count}, {random_pause} sec.')
        time.sleep(random_pause)

        csv_item = parse_tire_id(session, csv_item, args_country)
        if csv_item:
            csv_items.append(csv_item)

        if UPDATE_NEW_PRICES:
            update_item_price_in_db(cursor, csv_item.kod, csv_item.new_price)
            conn.commit()

    if csv_items:
        write_to_csv(csv_items, args_country)

    cursor.close()




