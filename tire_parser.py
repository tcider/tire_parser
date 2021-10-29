import os
import random

import requests
from bs4 import BeautifulSoup

OUR_COMPANY_ID = "204010"
MIN_VALUE = 4


class ParsedData:
    priceek: None
    wholesalerid: None
    stock: None

    def __init__(self, priceek, wholesalerid, stock):
        self.priceek = priceek
        self.wholesalerid = wholesalerid
        self.stock = stock


COUNTRIES = {
    "de": "https://tyre24.alzura.com/de/de/item/details/id/T",
    "fr": "https://tyre24.alzura.com/fr/fr/item/details/id/T",
    "it": "https://tyre24.alzura.com/it/it/item/details/id/T",
    "at": "https://tyre24.alzura.com/at/de/item/details/id/T",
    "be": "https://tyre24.alzura.com/be/nl/item/details/id/T",
    "pl": "https://tyre24.alzura.com/pl/pl/item/details/id/T",
}


WEB_BROWSER_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko)",
    "Mozilla/5.0 (iPad; CPU OS 9_3_5 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13G36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko"
]


class TireParser:

    def __init__(self):
        self.cookies = {
            'PHPSESSID': 'vuqlhui3ogrt64647cseh3l46l',
            'weather': '1',
            'redex_tyre': 'eyJzb3J0IjoicHJpb3JpdHk6ZGVzYyJ9',
            '__hs_opt_out': 'no',
            'SLG_wptGlobTipTmp': '1',
            'SLG_LNG_TRIGGER': '0',
            'SLG_G_WPT_TO': 'cs',
            'SLG_AUTO_TMP': '1',
            'SLG_GWPT_Show_Hide_tmp': '2',
            'alzura-cookie-consent': '%7B%22alzura%22%3Atrue%2C%22cloudflare%22%3Atrue%2C%22paypal%22%3Atrue%2C%22googleTagManager%22%3Atrue%2C%22googleAnalytics%22%3Atrue%2C%22facebook%22%3Atrue%2C%22googleAds%22%3Atrue%2C%22adobe%22%3Atrue%2C%22hubSpot%22%3Atrue%2C%22hotjar%22%3Atrue%7D',
            '__gads': 'ID=648b542cf59fe063:T=1620063710:S=ALNI_MYJpfj0-QqcD4hOTej-rDqnuNJkBg',
        }
        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://tyre24.alzura.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': WEB_BROWSER_USER_AGENTS[random.randint(0, len(WEB_BROWSER_USER_AGENTS) - 1)],
            'Accept': '*/*',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://tpc.googlesyndication.com/',
            'Accept-Language': 'en-US,en;q=0.9',
            'authority': 'pagead2.googlesyndication.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36 OPR/75.0.3969.243',
            'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'image',
            'referer': 'https://tyre24.alzura.com/',
            'accept-language': 'en-US,en;q=0.9',
            'If-None-Match': 'W/"PSA-aj-6umn3OQb9w"',
            'origin': 'https://tyre24.alzura.com',
            'X-Requested-With': 'XMLHttpRequest',
            'if-none-match': '"1616005470650935"',
            'cookie': 'RUL=EL6qyv4FGL6Rz40GIpMEATZhkON3Q2kMMz_XgScMmlayTaVghlsluKpIKClMAi-x3TQzP4i8i-Jj2fFHATeN_H51rBDb-mRbDMyY_DWAiAhLZUmZmvavdQakhnMRSvdpCGU9WEiXgvV-fbMcN0_p3WNZMh72WxPzjW0pNfk5f9GvC2g5IHe9a1YcavQrzUkojhR3fQrVKeFpiJzjjiBafSbwcUAxak6Vbi60nHImZPCzqZ2fW3wyAv5MN4fcozLEjQrEyqfjnrGPmNzC9pBmqoXhMOtcYWLVkPrI1XFRkmDEo66QfBIR0vVszQCOw7dIyCdUUpForN7RodL8hZLbzDQnFWryCFWWBgUOY3C0QZBnUdWZ-21oe0704JV450djCFWqx1lUDIG6yxrvGbKq43vLQ3ZVNPt_eQTt9rIrtOK_Q12SYzGzjV2yTf8lREg9i1TnsI_Lsl-Kn6K-XjS0i4IkxiTrXWf6NeCSdfrnfPtUXXeCShS15-NfX1oYt1t1fkM0gzN4hR8vV-RGMMnhRhSHpZDgJMedRJfUfFTe4QYMS42CjM_fvSo-g8FivvNEalVp3u5Sdhyt2dTuvOX6k8HJmlbtuvZH48pEIOdhMeoqchoerf53nHRPLTZ6uyFaQvrOOe3X-mpw21_dH0FjOxOlrcvUWmE1QT6BlGS4OUsdYm2KrBeJpCTICUWIUWahlBGh-u2eQ0Brpf1OymDtontK|cs=AP6Md-WvggSMguAJBbokpvwUrcW0; DSID=AAO-7r5kjJShklvBYpUcX2SkWncGl4bg4D9yFBds-eRTvyJaE3Td5wzU8m-rUvHiHRnH_omujVw5FMmLJlpwVzeWDhBsvBlheO1R0RBsf4t3uKukaLxdVnc; IDE=AHWqTUkucAoI71WC_4xE1XIPbJu49mkP0iVdl48iYz_e-d7VVBTrGIEXwSrmk6xe',
            'purpose': 'prefetch',
            'cache-control': 'max-age=0',
        }

    def login(self):
        data = {
            'userid': LOGIN_FROM_CONFIG,
            'password': PASSWORD_FROM_CONFIG
        }
        s = requests.Session()
        s.post(
            'https://tyre24.alzura.com/fr/fr/user/login/page/',
            headers=self.headers,
            cookies=self.cookies,
            data=data
        )
        return s

    def parse_table(self, html_text, table_class_name):
        soup = BeautifulSoup(html_text, 'lxml')
        # print(f"table === {table_class_name} ===")
        tables = soup.find_all('table', {'class': table_class_name})

        items = tuple()

        for table in tables:
            tbody = table.find('tbody')
            trs = tbody.find_all('tr')

            # tags = tbody.find_all('tr')[:2]

            for tr in trs:
                tag_data = dict((key.lower(), value) for key, value in tr.attrs.items())
                parsed_data = ParsedData(None, None, None)

                if 'data-priceek' in tag_data:
                    # print(f"data-priceek = {tag_data['data-priceek']}")
                    parsed_data.priceek = tag_data['data-priceek']
                if 'data-wholesalerid' in tag_data:
                    if str(tag_data['data-wholesalerid']) == OUR_COMPANY_ID:
                        # print('Found data-wholesalerid with our company. Skip...')
                        continue
                    # print(f"data-wholesalerid = {tag_data['data-wholesalerid']}")
                    parsed_data.wholesalerid = tag_data['data-wholesalerid']

                    td = tr.find('td', {'class': 'dealer-stock-block'})
                    stock = self._extract_digits(td.text)
                    if stock and stock > MIN_VALUE:
                        parsed_data.stock = stock
                        items += (parsed_data,)

        return items

    def _extract_digits(self, value):
        return int("".join([char for char in str(value) if char.isdigit()]))

    def parse_tire(self, session, tire_id, country):
        url = COUNTRIES[country] + str(tire_id)
        print(f"Parsing url: {url}")
        html_text = session.get(url).text
        # with open(f"data/{tire_id}__{country}.html", "w") as f:
        #     f.write(html_text)

        parsed_items = self.parse_table(html_text, 'table-basic-supplier')
        return parsed_items

