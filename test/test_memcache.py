import unittest
import logging
import collection_cache
import random,string
from google.appengine.api import memcache




class TestMemcache(unittest.TestCase):
        def test_set_get(self):
            cache = collection_cache.CollectionCache(480)
            cache.add(["test","test2"])
            self.assertEqual(len(cache.contents),1)
            results = memcache.get(cache.contents[0])
            self.assertEqual(len(results),2)

        def test_set_ge2t(self):
            cache = collection_cache.CollectionCache(480)
            hash = cache.add(["test","test2"])
            results = memcache.get(hash)
            self.assertEqual(len(results),2)


        def test_set_get_multi(self):
            cache = collection_cache.CollectionCache(480)
            cache.add(["test","test2"])
            cache.add({"test":"test2"})
            results = memcache.get_multi(cache.contents)
            self.assertEqual(len(results),2)

        def test_set_get_fetchAll(self):
            cache = collection_cache.CollectionCache(480)
            h1 = cache.add(["test","test2"])
            h2 =cache.add({"test":"test2"})
            results = cache.fetchAll()
            self.assertEqual(len(results),2)
            self.assertEqual(results[0][0],h1)
            self.assertEqual(len(results[0][1]),2)
            self.assertEqual(results[0][1][0],'test')



        def test_set_get_fetchAllLoop(self):
            cache = collection_cache.CollectionCache(480)
            h1 = cache.add(["test","test2"])
            h2 =cache.add({"test":"test2"})
            for key,results in cache.fetchAll():
                logging.info(key)

        def test_set_get_fetchAllLoopGen(self):
            cache = collection_cache.CollectionCache(480)
            h1 = cache.add(["testa","test1"])
            h2 =cache.add({"testb":"test2"})
            for key,results in cache.fetchAll():
                o = results

            self.assertEqual(o,{"testb":"test2"})


        def test_fetchAllLoop_none(self):
            cache = collection_cache.CollectionCache(480,"foo")
            for key,results in cache.fetchAll():
                logging.info(key)

        def test_Missing(self):
            cache = collection_cache.CollectionCache(480)
            h1 = cache.add(["test","test2"])
            h2 =cache.add({"test2":"test2"})
            memcache.delete(h1)
            results = cache.fetchAll()
            self.assertFalse (results[0][1])
            self.assertEqual(results[1][1]['test2'],'test2')

        def test_full(self):
            cache = collection_cache.CollectionCache(480)
            cache.add(["test","test2"])
            cache.add({"test":"test2"})
            key = cache.commit();
            cache = collection_cache.CollectionCache(480,key)
            results = cache.fetchAll()
            self.assertEqual(len(results),2)
            self.assertEqual(results[0][1][0],'test')

        def test_overflow(self):
            cache = collection_cache.CollectionCache(480)
            x = ''.join(random.choice(string.lowercase) for i in range(1005000))
            try:
                cache.add(["test",x])

            except ValueError:
                pass


