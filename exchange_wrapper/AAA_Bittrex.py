import time
import hmac
import pandas as pd
import hashlib
try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import urljoin
import requests

try:
    from Crypto.Cipher import AES
    import getpass, ast, json
    encrypted = True
except ImportError:
    encrypted = False
   
BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

BASE_URL = 'https://bittrex.com/api/v1.1/%s/'

MARKET_SET = {
    'getopenorders',
    'cancel',
    'sellmarket',
    'selllimit',
    'buymarket',
    'buylimit'
}

ACCOUNT_SET = {
    'getbalances',
    'getbalance',
    'getdepositaddress',
    'withdraw',
    'getorderhistory',
    'getorder',
    'getdeposithistory',
    'getwithdrawalhistory'
}

def encrypt(api_key, api_secret, export=True, export_fn='secrets.json'):
    cipher = AES.new(getpass.getpass('Input encryption password (string will not show)'))
    api_key_n = cipher.encrypt(api_key)
    api_secret_n = cipher.encrypt(api_secret)
    api = {'key': str(api_key_n), 'secret': str(api_secret_n)}
    if export:
        with open(export_fn, 'w') as outfile:
            json.dump(api, outfile)
    return api

def using_requests(request_url, apisign):
    return requests.get(
                request_url,
                headers={"apisign": apisign}
            ).json()
            
class Bittrex(object):
    """
    Used for requesting Bittrex with API key and API secret
    """
    def __init__(self, api_key, api_secret, dispatch=using_requests):
        self.api_key = str(api_key) if api_key is not None else ''
        self.api_secret = str(api_secret) if api_secret is not None else ''
        self.dispatch = dispatch

    def decrypt(self):
        if encrypted:
            cipher = AES.new(getpass.getpass('Input decryption password (string will not show)'))
            try:
                self.api_key = ast.literal_eval(self.api_key) if type(self.api_key) == str else self.api_key
                self.api_secret = ast.literal_eval(self.api_secret) if type(self.api_secret) == str else self.api_secret
            except:
                pass
            self.api_key = cipher.decrypt(self.api_key).decode()
            self.api_secret = cipher.decrypt(self.api_secret).decode()
        else:
            raise ImportError('"pycrypto" module has to be installed')

    def api_query(self, method, options=None):
        """
        Queries Bittrex with given method and options
        :param method: Query method for getting info
        :type method: str
        :param options: Extra options for query
        :type options: dict
        :return: JSON response from Bittrex
        :rtype : dict
        """
        if not options:
            options = {}
        nonce = str(int(time.time() * 1000))
        method_set = 'public'

        if method in MARKET_SET:
            method_set = 'market'
        elif method in ACCOUNT_SET:
            method_set = 'account'

        print(method)
        print(method_set)
        request_url = (BASE_URL % method_set) + method + '?'

        if method_set != 'public':
            request_url += 'apikey=' + self.api_key + "&nonce=" + nonce + '&'

        request_url += urlencode(options)

        apisign = hmac.new(self.api_secret.encode(),
                           request_url.encode(),
                           hashlib.sha512).hexdigest()
        return self.dispatch(request_url, apisign)

    def get_markets(self):
        """
        Used to get the open and available trading markets
        at Bittrex along with other meta data.
        :return: Available market info in JSON
        :rtype : dict
        """
        return self.api_query('getmarkets')

    def get_currencies(self):
        """
        Used to get all supported currencies at Bittrex
        along with other meta data.
        :return: Supported currencies info in JSON
        :rtype : dict
        """
        return self.api_query('getcurrencies')

    def get_ticker(self, market):
        """
        Used to get the current tick values for a market.
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        return self.api_query('getticker', {'market': market})

    def get_market_summaries(self):
        """
        Used to get the last 24 hour summary of all active exchanges
        :return: Summaries of active exchanges in JSON
        :rtype : dict
        """
        return self.api_query('getmarketsummaries')

    def get_marketsummary(self, market):
        """
        Used to get the last 24 hour summary of all active exchanges in specific coin
        :param market: String literal for the market(ex: BTC-XRP)
        :type market: str
        :return: Summaries of active exchanges of a coin in JSON
        :rtype : dict
        """
        return self.api_query('getmarketsummary', {'market': market})

    def get_orderbook(self, market, depth_type, depth=20):
        """
        Used to get retrieve the orderbook for a given market
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param depth_type: buy, sell or both to identify the type of orderbook to return.
            Use constants BUY_ORDERBOOK, SELL_ORDERBOOK, BOTH_ORDERBOOK
        :type depth_type: str
        :param depth: how deep of an order book to retrieve. Max is 100, default is 20
        :type depth: int
        :return: Orderbook of market in JSON
        :rtype : dict
        """
        return self.api_query('getorderbook', {'market': market, 'type': depth_type, 'depth': depth})

    def get_market_history(self, market, count):
        """
        Used to retrieve the latest trades that have occurred for a
        specific market.
        /market/getmarkethistory
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param count: Number between 1-100 for the number of entries to return (default = 20)
        :type count: int
        :return: Market history in JSON
        :rtype : dict
        """
        return self.api_query('getmarkethistory', {'market': market, 'count': count})


ser = pd.read_json("secrets.json", typ='series')
secrets = ser.to_frame('count')
api_key = secrets.iloc[0,0]
api_secret = secrets.iloc[1,0]

bittrex = Bittrex(api_key, api_secret)
#bittrex.get_markets()
bittrex.get_orderbook(market = 'BTC-NEO', depth_type = BUY_ORDERBOOK)
