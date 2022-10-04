import math
import requests
import json

import config

# Functions
def get_binance_rate(params):
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    binance_params = {
        "asset": "USDT",
        "page": 1,
        "rows": 1,
    }
    binance_params.update(params)
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.request("POST", url, data=json.dumps(binance_params), headers=headers)

    return float(response.json().get("data")[0].get("adv").get("price"))

def get_korona_rate(params):
    korona_url = "https://koronapay.com/transfers/online/api/transfers/tariffs"
    korona_params = {
        "sendingCountryId": "RUS",
        "sendingCurrencyId": "810",
        "paymentMethod": "debitCard",
        "receivingAmount": "10000",
        "receivingMethod": "cash",
        "paidNotificationEnabled": "false",
    }
    korona_params.update(params)
    headers = {
        "User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    }
    request = requests.get(korona_url, params=korona_params, headers=headers)

    return request.json()[0].get("exchangeRate")

def send_msg(text):
    params = {
        "chat_id": config.chat_id,
        "text": text,
        "parse_mode": "html",
    }
    url_req = "https://api.telegram.org/bot" + config.token + "/sendMessage"

    requests.get(url_req, params=params)

def add_fee(sum, fee):
    return math.ceil(10000 * sum / (1 - fee / 100)) / 10000

def calc_spread(buy, sell):
    return math.ceil(10000 * (sell / buy - 1)) / 100

def print_spread(spread):
    if (spread > 1):
        return f"<b>{spread}%</b>"

    if (spread >= 0):
        return f"{spread}%"

    return f"<s>{spread}%</s>"

def turkey_try_to_usdt(rate, fee):
    usdt_rate = get_binance_rate({
        "fiat": "TRY",
        "tradeType": "Buy",
        "payTypes": ["KoronaPay"]
    })    

    return add_fee(rate * usdt_rate, fee)

bundles = [
    {
        "name": "\U0001f1f9\U0001f1f7 \u20BA",
        "tag": "turkey_try",
        "korona_params": {
            "receivingCountryId": "TUR",
            "receivingCurrencyId": "949",
        },
        "fee_function": turkey_try_to_usdt,
    },
    {
        "name": "\U0001f1f9\U0001f1f7 $",
        "tag": "turkey_usd",
        "korona_params": {
            "receivingCountryId": "TUR",
            "receivingCurrencyId": "840",
        },
    },
    {
        "name": "\U0001f1f9\U0001f1f7 \u20AC",
        "tag": "turkey_eur",
        "korona_params": {
            "receivingCountryId": "TUR",
            "receivingCurrencyId": "978",
        },
    },
    {
        "name": "\U0001F1EC\U0001F1EA $",
        "tag": "georgia_usd",
        "korona_params": {
            "receivingCountryId": "GEO",
            "receivingCurrencyId": "840",
        },
    },
]

# Load data
try:
  data = json.load(open(config.file_name, "r"))
except:
  data = {}

fees_data = requests.get(config.fees_url).json()

usdt_sell = get_binance_rate({
    "fiat": "RUB",
    "tradeType": "Sell",
    "payTypes": ["TinkoffNew", "RosBankNew", "RaiffeisenBank"]
})

spreads = ""
rates = ""
fees = ""
new_data = {
    "usdt_sell": usdt_sell,
}

is_changed = False

for bundle in bundles:
    name = bundle.get("name", "")
    tag = bundle.get("tag", "")
    korona_params = bundle.get("korona_params", {})
    fee_function = bundle.get("fee_function", add_fee)

    fee = fees_data.get(tag, config.default_fee)
    rate = get_korona_rate(korona_params)
    rate_with_fee = fee_function(rate, fee)
    spread = calc_spread(rate_with_fee, usdt_sell)

    spreads += f"{name} {print_spread(spread)}\n"
    rates += f"\U0001F451{name} {rate} ({rate_with_fee})\n"
    fees += f"\U0001F4B1{name} {fee}%\n"

    new_data[tag] = spread
    old_spread = data.get(tag, 0)

    if (spread > 0 and abs(old_spread - spread) >= 0.5):
        is_changed = True

if (is_changed is True):
    send_msg(spreads + "\n" + rates + "\n" + fees + "\n" + f"\u2B05 {usdt_sell} \u20BD")

json.dump(new_data, open(config.file_name, "w+"))
