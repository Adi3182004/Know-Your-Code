class QueryCache:
    def __init__(self):
        self.cache = {}

    def get(self, query: str):
        return self.cache.get(query.lower())

    def set(self, query: str, value):
        self.cache[query.lower()] = value