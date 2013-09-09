import uuid
from google.appengine.api import memcache

class CollectionCache:


    def __init__(self, timeout=480, hash=None):
        self.contents = [];
        if hash:
            self.contents = memcache.get(hash)
        self.timeout = timeout

    def add(self, item):
        hash = uuid.uuid1().hex
        memcache.add(hash, item, time = self.timeout)
        self.contents.append(hash)
        return hash

    def commit(self):
        hash = uuid.uuid1().hex
        memcache.add(hash, self.contents, time = self.timeout)
        return hash


    def fetchAll(self):
        if not self.contents:
            return []
        return  [[key,memcache.get(key)] for key in self.contents]

    def fetch(self):
        for key in self.contents:
            item = memcache.get(key)
            if item:
                yield key,item