from wex import Client


client = Client('your-API-key', 'your-API-secret')

market_info = client.info()
my_orders = client.active_orders('btc_usd')
