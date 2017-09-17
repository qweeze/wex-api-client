import time
import json
import hashlib
import hmac
import warnings
try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError


class APIError(Exception):
    pass


__all__ = ('Client',)


class Client:

    PUBLIC_API_URL = 'https://wex.nz/api/3'
    TRADE_API_URL = 'https://wex.nz/tapi'

    def __init__(self, api_key=None, secret=None):
        self.api_key = api_key
        self.secret = secret
        if not all((api_key, secret)):
            warnings.warn('No API key and secret provided, private methods will be unavailable')
        else:
            self.api_key, self.secret = self.api_key.encode(), self.secret.encode()

    def _public_api_call(self, method_name, pair=(), **params):
        resp = urlopen('{url}/{method}/{pair}?{params}'.format(
            url=self.PUBLIC_API_URL,
            method=method_name,
            pair='-'.join(pair) if isinstance(pair, (list, tuple)) else pair,
            params=urlencode(params))
        )
        result = json.loads(resp.read().decode('utf-8'))
        if result.get('success') == 0:
            raise APIError(result.get('error', 'Unknown API error'))
        return result

    def _trade_api_call(self, method_name, **params):
        if not all((self.api_key, self.secret)):
            raise APIError('API key and secret must be provided to use private methods')

        nonce = int(time.time() * 10 % 1e9)
        data = {
            'method': method_name,
            'nonce': nonce
        }
        for k, v in params.items():
            if v is None:
                continue
            data[k.rstrip('_')] = v

        H = hmac.new(self.secret, digestmod=hashlib.sha512)
        H.update(urlencode(data).encode())
        sign = H.hexdigest()

        req = Request(self.TRADE_API_URL)
        req.add_header('Key', self.api_key)
        req.add_header('Sign', sign)
        resp = urlopen(req, urlencode(data).encode())
        result = json.loads(resp.read().decode('utf-8'))
        if result.get('success') == 0:
            raise APIError(result.get('error', 'Unknown API error'))
        return result

    def info(self):
        """
        This method provides all the information about currently active pairs, such as the maximum
        number of digits after the decimal point, the minimum price, the maximum price, the minimum transaction size,
        whether the pair is hidden, the commission for each pair.
        """
        return self._public_api_call('info')

    def ticker(self, pair, ignore_invalid=0):
        """
        This method provides all the information about currently active pairs, such as: the maximum price,
        the minimum price, average price, trade volume, trade volume in currency, the last trade, Buy and Sell price.
        All information is provided over the past 24 hours.
        :param str or iterable pair: pair (ex. 'btc_usd' or ['btc_usd', 'eth_usd'])
        :param int ignore_invalid: ignore non-existing pairs
        """
        return self._public_api_call('ticker', pair=pair, ignore_invalid=ignore_invalid)

    def depth(self, pair, limit=150, ignore_invalid=0):
        """
        This method provides the information about active orders on the pair.
        :param str or iterable pair: pair (ex. 'btc_usd' or ['btc_usd', 'eth_usd'])
        :param limit: how many orders should be displayed (150 by default, max 5000)
        :param int ignore_invalid: ignore non-existing pairs
        """
        return self._public_api_call('depth', pair=pair, limit=limit, ignore_invalid=ignore_invalid)

    def trades(self, pair, limit=150, ignore_invalid=0):
        """
        This method provides the information about the last trades.
        :param str or iterable pair: pair (ex. 'btc_usd' or ['btc_usd', 'eth_usd'])
        :param limit: how many orders should be displayed (150 by default, max 5000)
        :param int ignore_invalid: ignore non-existing pairs
        """
        return self._public_api_call('trades', pair=pair, limit=limit, ignore_invalid=ignore_invalid)

    def get_info(self):
        """
        Returns information about the user`s current balance, API-key privileges, the number of open orders and
        Server Time.
        To use this method you need a privilege of the key info.
        """
        return self._trade_api_call('getInfo')

    def trade(self, pair, type_, rate, amount):
        """
        The basic method that can be used for creating orders and trading on the exchange.
        To use this method you need an API key privilege to trade.
        You can only create limit orders using this method, but you can emulate market orders using rate parameters.
        E.g. using rate=0.1 you can sell at the best market price.
        Each pair has a different limit on the minimum / maximum amounts, the minimum amount and the number of digits
        after the decimal point. All limitations can be obtained using the info method in PublicAPI v3.

        :param str pair: pair (ex. 'btc_usd')
        :param str type_: order type ('buy' or 'sell')
        :param float rate: the rate at which you need to buy/sell
        :param float amount: the amount you need to buy/sell
        """
        return self._trade_api_call('Trade', pair=pair, type_=type_, rate=rate, amount=amount)

    def active_orders(self, pair=None):
        """
        Returns the list of your active orders.
        To use this method you need a privilege of the info key.
        If the order disappears from the list, it was either executed or canceled.

        :param str or None pair: pair (ex. 'btc_usd')
        """
        return self._trade_api_call('ActiveOrders', pair=pair)

    def order_info(self, order_id):
        """
        Returns the information on particular order.
        To use this method you need a privilege of the info key.

        :param int order_id: order ID
        """
        return self._trade_api_call('OrderInfo', order_id=order_id)

    def cancel_order(self, order_id):
        """
        This method is used for order cancellation.
        To use this method you need a privilege of the trade key.

        :param int order_id: order ID
        """
        return self._trade_api_call('CancelOrder', order_id=order_id)

    def trade_history(
        self, from_=None, count=None, from_id=None, end_id=None,
        order=None, since=None, end=None, pair=None
    ):
        """
        Returns trade history.
        To use this method you need a privilege of the info key.

        :param int or None from_: trade ID, from which the display starts (default 0)
        :param int or None count: the number of trades for display	(default 1000)
        :param int or None from_id: trade ID, from which the display starts	(default 0)
        :param int or None end_id: trade ID on which the display ends (default inf.)
        :param str or None order: sorting (default 'DESC')
        :param int or None since: the time to start the display (default 0)
        :param int or None end: the time to end the display	(default inf.)
        :param str or None pair: pair to be displayed (ex. 'btc_usd')
        """
        return self._trade_api_call(
            'TradeHistory', from_=from_, count=count, from_id=from_id, end_id=end_id,
            order=order, since=since, end=end, pair=pair
        )

    def trans_history(
            self, from_=None, count=None, from_id=None, end_id=None,
            order=None, since=None, end=None
    ):
        """
        Returns the history of transactions.
        To use this method you need a privilege of the info key.

        :param int or None from_: transaction ID, from which the display starts (default 0)
        :param int or None count: number of transaction to be displayed	(default 1000)
        :param int or None from_id: transaction ID, from which the display starts (default 0)
        :param int or None end_id: transaction ID on which the display ends	(default inf.)
        :param str or None order: sorting (default 'DESC')
        :param int or None since: the time to start the display (default 0)
        :param int or None end: the time to end the display	(default inf.)
        """
        return self._trade_api_call(
            'TransHistory', from_=from_, count=count, from_id=from_id, end_id=end_id,
            order=order, since=since, end=end
        )

    def coin_deposit_address(self, coin_name):
        """
        This method can be used to retrieve the address for depositing crypto-currency.
        To use this method, you need the info key privilege.
        At present, this method does not generate new adresses. If you have never deposited in a particular
        crypto-currency and try to retrive a deposit address, your request will return an error, because this address
        has not been generated yet.

        :param str coin_name: crypto currency (ex. 'BTC')
        """
        return self._trade_api_call('CoinDepositAddress', coinName=coin_name)

    def withdraw_coin(self, coin_name, amount, address):
        """
        The method is designed for cryptocurrency withdrawals.
        Please note: You need to have the privilege of the Withdraw key to be able to use this method. You can make
        a request for enabling this privilege by submitting a ticket to Support.
        You need to create the API key that you are going to use for this method in advance. Please provide the first
        8 characters of the key (e.g. HKG82W66) in your ticket to support. We'll enable the Withdraw privilege for
        this key.
        When using this method, there will be no additional confirmations of withdrawal. Please note that you are
        fully responsible for keeping the secret of the API key safe after we have enabled the Withdraw
        privilege for it.

        :param str coin_name: currency (ex. 'BTC')
        :param int amount: withdrawal amount
        :param str address: withdrawal address
        """
        return self._trade_api_call('WithdrawCoin', coinName=coin_name, amount=amount, address=address)

    def create_coupon(self, currency, amount, receiver):
        """
        This method allows you to create Coupons.
        Please, note: In order to use this method, you need the Coupon key privilege. You can make a request to
        enable it by submitting a ticket to Support..
        You need to create the API key that you are going to use for this method in advance. Please provide
        the first 8 characters of the key (e.g. HKG82W66) in your ticket to support. We'll enable the Coupon privilege
        for this key.
        You must also provide us the IP-addresses from which you will be accessing the API.
        When using this method, there will be no additional confirmations of transactions. Please note that you are
        fully responsible for keeping the secret of the API key safe after we have enabled the Withdraw
        privilege for it.

        :param str currency: currency (ex. 'BTC')
        :param int amount: withdrawal amount
        :param str receiver: name of user who is allowed to redeem the code
        """
        return self._trade_api_call('CreateCoupon', currency=currency, amount=amount, receiver=receiver)

    def redeem_coupon(self, coupon):
        """
        This method is used to redeem coupons.
        Please, note: In order to use this method, you need the Coupon key privilege. You can make a request
        to enable it by submitting a ticket to Support..
        You need to create the API key that you are going to use for this method in advance. Please provide
        the first 8 characters of the key (e.g. HKG82W66) in your ticket to support. We'll enable the Coupon
        privilege for this key.
        You must also provide us the IP-addresses from which you will be accessing the API.
        When using this method, there will be no additional confirmations of transactions. Please note that you are
        fully responsible for keeping the secret of the API key safe after we have enabled the Withdraw
        privilege for it.

        :param str coupon: coupon (ex. 'WEXUSD...')
        """
        return self._trade_api_call('RedeemCoupon', coupon=coupon)
