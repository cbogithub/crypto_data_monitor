import numpy as np
import ccxt
from threading import Thread
import time
from getter import Candles, OrderBook
from store import CsvStore, SqlStore, NoSqlStore

class ExchangeWorker(Thread):

    """ExchangeWorker: individual connection with an exchange to retrieve data"""

    def __init__(self, exchange, symbols, symbol_freq, req_freq, data_type, database_type,
                 mutex, barrier):
        
        Thread.__init__(self)
        self.symbols = symbols
        self.symbol_freq = symbol_freq
        self.req_freq = req_freq
        self.client = getattr(ccxt, exchange.lower())()
        
        table_prefix = data_type
        directory = "./"+data_type
        if database_type == "csv":
            route = "./"+data_type+"/"
            db = CsvStore(route, table_prefix)
        elif database_type == "sql":
            route = "sqlite:///"+directory+"/data.db"
            db = SqlStore(route, table_prefix)
        elif database_type == "nosql":
            db = NoSqlStore(table_prefix) 
        else:
            raise ValueError("Invalid database_type: '"+database_type+"'.")

        if data_type.lower() == "candles":
            self.data = Candles(exchange, self.client, mutex, barrier, db)
        elif data_type.lower() == "orderbook":
            self.data = OrderBook(exchange, self.client, mutex, barrier, db)
        else:
            raise("Invalid data_type: '"+data_type+"'.")
    
    def run(self):
        
        while True:

            for symbol in self.symbols:

                start_req_time = time.time()
                while int(time.time()-start_req_time) <= self.client.rateLimit/1000:
                    pass
                self.require_data(symbol)

    def require_data(self,symbol):
        self.data.request(symbol)