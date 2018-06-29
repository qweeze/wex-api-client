import unittest

from wex.client import Client


class TetClient(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def test_info(self):
        result = self.client.info()
        assert 'pairs' in result

    def test_ticker(self):
        result = self.client.ticker(['btc_usd', 'eth_usd'])
        assert result['btc_usd']['high'] >= result['btc_usd']['low']

    def test_depth(self):
        result = self.client.depth('btc_usd', 'fake_fake', ignore_invalid=1)
        assert all(k in ('bids', 'asks') for k in result['btc_usd'].keys())

    def test_trades(self):
        result = self.client.trades('btc_usd', limit=21)
        assert len(result['btc_usd']) == 21


if __name__ == '__main__':
    unittest.main()
