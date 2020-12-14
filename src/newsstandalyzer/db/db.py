from pymongo import MongoClient


class NewsDB:

    def __init__(self, host, port, db, collection):
        self.client = MongoClient(host, port)
        self.db = self.client[db]
        self.col = self.db[collection]
