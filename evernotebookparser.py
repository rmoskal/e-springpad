__author__ = 'rob'

import sys, os
from xml.etree import ElementTree
from xml.dom import pulldom
import xml.sax

def slurp(filename):
    """returns a file as a string"""
    f = open(filename, 'r')
    contents = f.readlines()
    f.close()
    return ''.join(contents)

def extract (data):
    start = data.find('<en-note>')
    end = data.find('</en-note>')
    return data[start+9:end]

def extract2 (data):

    start = data.find('<en-note')
    data = data[start:]
    start = data.find('>')
    end = data.find('</en-note>')
    return data[start+1:end].strip()




class NotebookParser:
    """returns a file as a string"""
    def __init__(self, contents=''):
        self.xml = ElementTree.fromstring(contents)

    def get_items(self):
        """Returns all the entries in the atom feed, decorating each with the tags"""
        results = []
        for e in self.xml:
            if e.tag != 'note': continue
            entry = {}
            if not self.checkItem(entry,e): continue
            results.append(entry)
        return results

    def checkItem(self,entry, e):
        tags = []
        for item in e.getchildren():
            if item.tag == 'tag':
                    tags.append(item.text)
            if item.tag == 'content':
                     entry["content"]= extract(item.text)
            if item.tag == 'title':
                     entry["title"]= item.text
            if item.tag == 'note-attributes':
                     u = item.findtext("source-url")
                     if u:
                         entry["url"]= u
            entry["tags"]=tags
        return True

class NotebookParser2:
    """returns a file as a string"""
    def __init__(self, contents=''):
        self.contents = contents



    def get_items(self,callback):
        events = pulldom.parse(self.contents)
        results = []
        for (event, node) in events:
            entry = {}
            if event == pulldom.START_ELEMENT:
                if node.tagName == 'note':
                    events.expandNode(node)
                    try:
                        if self.fillItem(entry,node):
                            callback(entry)  
                    except (MemoryError,ValueError):
                         pass
        return results

    def fillItem(self, entry,node):
        tags = []
        entry['title'] = getText(node.getElementsByTagName("title")[0].childNodes)

        entry['content'] = extract2(getText(node.getElementsByTagName("content")[0].childNodes))

        if len (node.getElementsByTagName("note-attributes"))>0:
            _node = node.getElementsByTagName("note-attributes")[0].getElementsByTagName('source-url')
            if _node:
                entry['url'] = getText(_node[0].childNodes)

        for tag in node.getElementsByTagName("tag"):
                tags.append(getText(tag.childNodes))

        entry['tags'] = tags
        return True

def getText(nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)