__author__ = 'rob'
import unittest
import logging
import evernotebookparser
from xml.etree import ElementTree
import re


class TestNotebookParser(unittest.TestCase):

        def setUp(self):
           self.o = evernotebookparser.NotebookParser2("../Quotes.enex")


        def test_parsing2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            self.assertEquals(32,len(results))


        def test_re(self):
            data = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
            <en-note>Barthes, Roland<br clear="none"/> Sade, Fourier, Loyola: p.7.<br clear="none"/>
            <br clear="none"/>Motto: It is a matter of bringing into daily life a fragment of the unintelligible formulas that emanate from a text we admire.
            <br clear="none"/></en-note>"""


            self.assertEquals(data.find('<en-note>'),133)
            self.assertEquals(data.find('</en-note>'),410)
            self.assertEquals(data[133],'<')

            data = evernotebookparser.extract(data)
            self.assertTrue(data.startswith("Barthes"))


        def test_construction1(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[0];
            self.assertEquals(["B"],item['tags'])
            self.assertTrue(item['content'].startswith("Barthes"))

        def test_construction2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[1];
            self.assertEquals(['O'],item['tags'])



class TestNotebookParser2(unittest.TestCase):

        def setUp(self):
           self.o = evernotebookparser.NotebookParser2("../test.enex")


        def test_parsing2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            self.assertEquals(2,len(results))

        def test_construction1(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[0];
            self.assertTrue(item['content'].startswith("<div>"))
            self.assertFalse("url" in item)

        def test_construction2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[1];
            self.assertTrue(item['content'].startswith("<div>"))
            self.assertTrue("url" in item)
            self.assertEquals(item['url'],"http://mostmedia.com")

class TestNotebookMac(unittest.TestCase):

        def setUp(self):
           self.o = evernotebookparser.NotebookParser2("../Travel.enex")


        def test_parsing2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            self.assertEquals(4,len(results))

        def test_construction1(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[0];
            self.assertTrue(item['content'].startswith("<div>"))
            self.assertFalse("url" in item)

        def test_construction2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[1];
            self.assertTrue(item['content'].startswith("<div>"))

class TestDavids(unittest.TestCase):

        def setUp(self):
           self.o = evernotebookparser.NotebookParser2("../recipes.enex")


        def test_parsing2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            self.assertEquals(49,len(results))

        def test_construction1(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[0];
            print item['content']
            #self.assertTrue(item['content'].startswith("<div>"))
            #self.assertFalse("url" in item)

        def test_construction2(self):
            results = [];
            self.o.get_items(lambda x: results.append(x))
            item = results[1];
            #self.assertTrue(item['content'].startswith("<div>"))
     


  