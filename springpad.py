#!/usr/bin/env python
# encoding: utf-8
"""
block.py

Created by Pete Aykroyd on 2010-06-21.
Copyright (c) 2010 Spring Partners. All rights reserved.

Visit http://springpadit.com/api/oauth-register-app to get your develope tokens
"""
import logging

import urllib, httplib2, uuid, time, calendar, sys
import oauth
from google.appengine.api import urlfetch
from django.utils import simplejson as json
from datetime import datetime
from time import mktime

BASE_API_URL = 'http://springpadit.com/api'
REQUEST_TOKEN_URL = '%s/oauth-request-token' % BASE_API_URL
ACCESS_TOKEN_URL = '%s/oauth-access-token' % BASE_API_URL
AUTHORIZATION_URL = '%s/oauth-authorize' % BASE_API_URL

STANDARD_HEADERS={'Content-Type':'application/json', 'X-Spring-Client':'Android'}

def default_get_block_store():
    """default function for retrieving the block_store... this is added for the sake of flexibility"""
    return SpringRpcService().block_store;

# overridable function to get the block store
get_block_store = default_get_block_store

# IMPORTANT: you need to request API access to get your authorization tokens to use this library.
# visit: http://springpadit.com/api/oauth-register-app
CONSUMER_TOKEN = '0aa8a414cfab4ba9acd4572f8be64521'
CONSUMER_PRIVATE = '6878054a5b844b248877d2c0b7d94265'

class Block:
    def __init__(self, blockMap={}):
        self.update_block(blockMap)

    def update_block(self, blockMap):
        """updates the block with the given block map. this function overwrites the existing block -- it does not merge"""
        self.blockMap = blockMap
        if 'properties' not in self.blockMap:
            self.blockMap['properties'] = {}
        else:
            for k in self.blockMap['properties'].keys():
                self.set(k, parse_value(self.blockMap['properties'][k]))

    def uuid():
        doc = "The uuid property."
        def fget(self):
            return parse_value(self.blockMap.get('uuid', None))
        def fset(self, value):
            self.blockMap['uuid'] = value
        return locals()
    uuid = property(**uuid())

    def name():
        doc = "The name property."
        def fget(self):
            return self.blockMap.get('name', None)
        def fset(self, value):
            self.blockMap['name'] = value
        return locals()
    name = property(**name())

    def creator():
        doc = """creator user uuid"""
        def fget(self):
            return parse_value(self.blockMap.get('creator', None))
        def fset(self, value):
            self.blockMap['creator'] = value
        return locals()
    creator = property(**creator())

    def creatorUsername():
        doc = """creator username"""
        def fget(self):
            return self.blockMap.get('creatorUsername', None)
        def fset(self, value):
            self.blockMap['creatorUsername'] = value
        return locals()
    creatorUsername = property(**creatorUsername())

    def creatorPicture():
        doc = """creator picture"""
        def fget(self):
            return self.blockMap.get('creatorPicture', None)
        def fset(self, value):
            self.blockMap['creatorPicture'] = value
        return locals()
    creatorPicture = property(**creatorPicture())

    def created():
        doc = "The created property."
        def fget(self):
            return parse_value(self.blockMap.get('created', None))
        def fset(self, value):
            self.blockMap['created'] = value
        return locals()
    created = property(**created())

    def modified():
        doc = "The modified property."
        def fget(self):
            return parse_value(self.blockMap.get('modified', None))
        def fset(self, value):
            self.blockMap['modified'] = value
        return locals()
    modified = property(**modified())

    def type():
        doc = "The type property."
        def fget(self):
            return parse_value(self.blockMap.get('type', None))
        def fset(self, value):
            self.blockMap['type'] = value
        return locals()
    type = property(**type())

    def set(self, propertyName, value):
        """sets the value"""
        if propertyName == 'name':
            self.name = value
        else:
            self.blockMap.get('properties')[propertyName] = self._ref(value)

    def get(self, propertyName):
        """returns the referenced property, inflating blocks as necessary"""
        if propertyName == 'name':
            return self.name
        else:
            properties = self.blockMap.get('properties')
            return self._deref(properties.get(propertyName, None))

    def add(self, propertyName, value):
        """adds a value to the block"""
        propertyList = self.blockMap['properties'].get(propertyName, None)

        if propertyList == None:
            propertyList = []
            self.blockMap['properties'][propertyName] = propertyList

        propertyList.append(self._ref(value))

    def remove(self, propertyName, value):
        """removes the value from the list"""
        values = self.blockMap['properties'][propertyName]
        if isinstance(value, Block):
            results = filter(lambda ref: ref.uuid == value.uuid, values)
            if len(results) == 0: return False
            values.remove(results[0])
        else:
            values.remove(value)
        return True

    def move(self, propertyName, value, toIndex):
        """moves the value to the given index"""

        values = self.blockMap['properties'][propertyName]
        if isinstance(value, Block):
            results = filter(lambda ref: ref.uuid == value.uuid, values)
            if len(results) == 0: return False
            values.remove(results[0])
            values.insert(toIndex, results[0])
        else:
            values.remove(value)
            values.insert(toIndex, value)
        return True

    def _owned(self):
        """returns true if the block is owned by the current user auth'd by SpringRpcService"""
        return self.creator == SpringRpcService().user_uuid

    def _ref(self, value):
        """creates and returns a BlockReference if necessary"""

        if isinstance(value, Block) and self._owned():
            return BlockReference(value.uuid)
        elif isinstance(value, list) and self._owned():
            return map(self._ref, value)
        else:
            return value

    def _deref(self, value):
        """dereferences value if it's a BlockReference"""
        if isinstance(value, BlockReference):
            return value.resolve()
        elif isinstance(value, list):
            return map(self._deref, value)
        else:
            return value

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class SimpleBlockStore(object):
    """
    Basic implementation of block storage. Uses a dict and keeps everything owned by the user in it.
    This can easily be overrided or entirely replaced by your own class with the same public interface.
    """

    def __init__(self):
        self._blocks = {}

    def inflate_block(self, dict_repr):
        """basic block inflater. creates a Block object from the dict and adds it to block store"""
        uuid = dict_repr.get('uuid', None)

        block = None

        if uuid != None:
            uuid = parse_uuid(uuid)
            block = self.get_block(uuid)

        if (block == None):
            block = Block(dict_repr)
            if SpringRpcService().user_uuid == block.creator or (block.creator == None and block.uuid != None):
                self.add_block(block)
        else:
            block.update_block(dict_repr)

        return block

    def add_block(self, block):
        """stores the block in the block store"""
        self._blocks[block.uuid] = block

    def get_block(self, uuid):
        """returns the block stored with that UUID or None"""
        return self._blocks.get(uuid, None)

    def remove_block(self, block):
        """removes the block from the store"""
        if block.uuid in self._blocks:
            self._blocks.pop(block.uuid)

    def count(self):
        return len(self._blocks)





class BlockReference:
    """simple reference to a block that is stored in block store"""
    def __init__(self, uuid):
        self.uuid = uuid

    def resolve(self):
        return get_block_store().get_block(self.uuid)

class SimpleFetcher:
    def __init__(self):
        self.http = httplib2.Http()
        self._token = None
        self._user = None
        self._password = None

    def fetch(self, url, parameters=None, post_data=None, headers={}, method='GET'):
        if parameters:
            parameters = dict([(k, parameters[k]) for k in filter(lambda x: parameters[x] != None, parameters)])
            paramStr = urllib.urlencode(parameters)
            url = "%s?%s" % (url, paramStr)

        headers.update(STANDARD_HEADERS)

        if self._token:
            headers.update({'X-Spring-Api-Token':self._token, 'X-Spring-Username':self._user, 'X-Spring-Password':self._password})

        print "%s" % url

        # for key in headers:
        #     print "%s: %s" % (key, headers[key])

        if post_data:
            resp, data = self.http.request("%s/%s" % (BASE_API_URL, url), method="POST", body=post_data, headers=headers)
        else:
            resp, data = self.http.request("%s/%s" % (BASE_API_URL, url), headers=headers, method=method)

        if resp.status != 200:
            if resp.status == 401 or resp.status == 403:
                raise SecurityException(resp.reason)
            raise Exception(resp.reason)

        return data

    def authenticate(self, username, password, token, rpc_service):
        """stores username, password, and app token for use in messages"""
        self._token = token
        self._user = username
        self._password = password
        # rpc_service.user_uuid = parse_uuid(result.get('uuid'))
        rpc_service.username = username


class OAuthFetcher:
    """ OAuth based on oauth implementation at: http://code.google.com/p/oauth-python-twitter/source/browse/trunk/oauthtwitter.py """

    def __init__(self, consumer_key, consumer_secret, access_token=None):
        self.http = httplib2.Http()
        self._consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
        self._signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self._access_token = access_token
        self._default_params = {}

    def hey(self, url,headers,payload):
        rpc = urlfetch.create_rpc(deadline=10.0)
        urlfetch.make_fetch_call(rpc, url, method=urlfetch.POST, headers=headers,payload=payload)
        resp = rpc.get_result()
        url_data = resp.content
        return resp, url_data

    def _FetchUrl(self, url, post_data=None, parameters=None, headers={}, no_cache=False):
        '''Fetch a URL, optionally caching for a specified time.

        Args:
            url: The URL to retrieve
            post_data:
                If set, POST will be used.
            parameters:
                A dict whose key/value pairs should encoded and added
                to the query string. [OPTIONAL]

        Returns:
            A string containing the body of the response.
        '''

        # Build the extra parameters dict


        extra_params = {}
        if self._default_params:
            extra_params.update(self._default_params)
        if parameters:
            extra_params.update(parameters)

        if post_data:
            http_method = "POST"
        else:
            http_method = "GET"

        req = self._makeOAuthRequest(url, parameters=extra_params, http_method=http_method)
        self._signRequest(req, self._signature_method)

        url = req.to_url()

        headers = {}
        headers.update(STANDARD_HEADERS)
        headers.update(headers)



        # Open and return the URL immediately
        if post_data:
            rpc = urlfetch.create_rpc(deadline=10.0)
            urlfetch.make_fetch_call(rpc, url, method=urlfetch.POST, headers=headers,payload=post_data)
            resp = rpc.get_result()
            url_data = resp.content
        else:
            rpc = urlfetch.create_rpc(deadline=10.0)
            urlfetch.make_fetch_call(rpc, url, method=urlfetch.GET, headers=headers,)
            resp = rpc.get_result()
            url_data = resp.content

        return url_data

    def _makeOAuthRequest(self, url, token=None, parameters=None, http_method="GET"):
        '''Make a OAuth request from url and parameters

        Args:
            url: The Url to use for creating OAuth Request
            parameters:
                 The URL parameters
            http_method:
                 The HTTP method to use
        Returns:
            A OAauthRequest object
        '''
        if not token:
            token = self._access_token

        request = oauth.OAuthRequest.from_consumer_and_token(self._consumer, token=token, http_url=url, parameters=parameters, http_method=http_method)
        return request

    def _signRequest(self, req, signature_method=oauth.OAuthSignatureMethod_HMAC_SHA1()):
        '''Sign a request

        Reminder: Created this function so incase
        if I need to add anything to request before signing

        Args:
            req: The OAuth request created via _makeOAuthRequest
            signate_method:
                 The oauth signature method to use
        '''
        req.sign_request(signature_method, self._consumer, self._access_token)

    def get_authorization_url(self, token, url=AUTHORIZATION_URL):
        '''Create a signed authorization URL

        Returns:
            A signed OAuthRequest authorization URL
        '''
        req = self._makeOAuthRequest(url, token=token)
        self._signRequest(req)
        return req.to_url()

    def get_access_token(self, url=ACCESS_TOKEN_URL):
        token = self._FetchUrl(url, no_cache=True)
        access_token = oauth.OAuthToken.from_string(token)
        self._access_token = access_token
        return access_token

    def get_request_token(self, url=REQUEST_TOKEN_URL):
        '''Get a Request Token from Twitter

        Returns:
            A OAuthToken object containing a request token
        '''
        resp = self._FetchUrl(url, no_cache=True)
        token = oauth.OAuthToken.from_string(resp)
        self._access_token = token
        return token

    def fetch(self, url, parameters=None, headers={}, post_data=None, method='GET'):
            if parameters:
                parameters = dict([(k, parameters[k]) for k in filter(lambda x: parameters[x] != None, parameters)])
                paramStr = urllib.urlencode(parameters)
                url = "%s?%s" % (url, paramStr)

            url = BASE_API_URL + "/" + url
            headers.update(STANDARD_HEADERS)
            print "%s" % url

            return self._FetchUrl(url, post_data, parameters, headers)

class ResponseFormat:
    RawHtml = 1
    Json = 2
    Blocks = 3

class SpringRpcService:
    """provides access to Springpad's API functions. all instances of this class share state"""
    __shared_state = {'token':None, 'fetcher': SimpleFetcher(), 'user_uuid':None, 'username':None, 'block_store':SimpleBlockStore() }

    def __init__(self):
        self.__dict__ = self.__shared_state

    def _process_response(self, data, format):
        if format == ResponseFormat.RawHtml:
            return data
        elif format == ResponseFormat.Json:
            return json.loads(data)
        else:
            val = json.loads(data)

            if isinstance(val, dict) and 'blocks' not in val:
                return self.block_store.inflate_block(val)
            elif isinstance(val, dict):
                return map(self.block_store.inflate_block, val['blocks'])
            else:
                return map(self.block_store.inflate_block, val)

    def set_user_context(self, username, uuid):
        """
        a number of functions of SpringRpcService rely on user information. This method should be set as soon as authentication
        is complete
        Arguments:
        - `username`: username field used by springpad
        - `uuid`: uuid used to identify the user in springpad
        """
        self.user_uuid = uuid
        self.username = username


    def get_block(self, uuid, resp_format=ResponseFormat.Blocks):
        """returns a block by the uuid"""
        return self._process_response(self.fetcher.fetch("users/me/blocks/%s" % uuid), resp_format)

    def get_blocks(self, type_filter=None, sort='created', order='desc', filter_string=None, limit=10, start=0, \
                       format='full', resp_format=ResponseFormat.Blocks):
        """returns some blocks"""

        params = {'sort':sort, 'order':order, 'limit':limit, 'start':start, 'format':format}
        if type_filter != None: params['type'] = type_filter
        if filter_string != None: params['filter'] = filter_string

        results = self.fetcher.fetch("users/me/blocks", parameters=params)

        return self._process_response(results, resp_format)

    def find_new_blocks(self, type_filter=None, text=None, location=None, limit=10, resp_format=ResponseFormat.Blocks):
        """
        searches springpad and the web for new blocks matching the parameters
        Arguments:
        - `type_filter`: name of the type or None
        - `text`: text to search for in the name or properties of the block
        - `location`: if specified, this can either be a string (e.g., Cambridge, MA) or a dict contain lat/lng information
        - `limit`: maximum number of results to return
        - `resp_format`: desired format of the response
        """
        params = {'limit':limit, 'text':text}

        if isinstance(location, str):
            if text == None:
                params['text'] = location
            else:
                params['text'] = text + ' ' + location
        elif isinstance(location, dict):
            params['lat'] = locations['lat']
            params['lng'] = locations['lng']

        if type_filter == None:
            return self._process_response(self.fetcher.fetch("/blocks/all", parameters=params), resp_format)
        else:
            return self._process_response(self.fetcher.fetch("/blocks/types/%s/all" % type_filter, \
                                                                 parameters=params), resp_format)

    def attach_file(self, uuid, bytes, filename=None, description=None):
        data = self.fetcher.fetch("/users/me/blocks/%s/files" % uuid, post_data=bytes, \
                                      parameters = {'filename':filename, 'description':description},
                                      method='POST')

        return True

    def attach_photo(self, uuid, bytes, filename=None, description=None):
        data = self.fetcher.fetch("/users/me/blocks/%s/photos" % uuid, post_data=bytes, \
                                      parameters = {'filename':filename, 'description':description},
                                      method='POST')

        return True


    def get_user(self, user_id, resp_format=ResponseFormat.Json):
        """takes either the user uuid, username, or email and fetches info about the user from springpad"""
        return self._process_response(self.fetcher.fetch("users/%s" % user_id), resp_format)

    def get_mutator(self):
        return Mutator(self)

    def new_uuid(self):
        """returns a uuid to assign to a new instance. must have authenticated for this to work"""
        uuid_str = str(uuid.uuid4())
        return self.user_uuid[:2] + '3' + uuid_str[3:]

    def execute_commands(self, commands):
        """executes commands on the server"""
        self.fetcher.fetch('users/me/commands', method='POST', post_data=json.dumps(commands))

class Mutator:
    """Mutator objects are used to capture changes to objects so that they can be sent to the server"""
    def __init__(self, rpc):
        self.commands = []
        self.rpc = rpc

    def set(self, block, propertyName, value):
        """sets a property on a block"""
        self.commands.append(['set', get_json_value(block.uuid), propertyName, get_json_value(value)])
        block.set(propertyName, value)

    def add(self, block, propertyName, value):
        """adds a value to a property on a block"""
        self.commands.append(['add', get_json_value(block.uuid), propertyName, get_json_value(value)])
        block.add(propertyName, value)

    def remove(self, block, propertyName, value):
        """removes a value from the block"""
        self.commands.append(['remove', get_json_value(block.uuid), propertyName, get_json_value(value)])
        block.remove(propertyName, value)

    def move(self, block, propertyName, value, toIndex):
        """move a value to the specified index"""
        self.commands.append(['move', get_json_value(block.uuid), propertyName, get_json_value(value), toIndex])
        block.move(propertyName, value, toIndex)

    def delete(self, block):
        """deletes the block"""
        self.commands.append(['delete', get_json_value(block.uuid)])

    def create(self, type_name):
        """creates a new block of the given type and returns it"""
        block = self.rpc.block_store.inflate_block({'uuid':self.rpc.new_uuid()})
        block.type = type_name
        self.commands.append(['create', type_name, get_json_value(block.uuid)])
        return block

    def commit(self):
        """commits changes in this transaction to the server"""
        self.rpc.execute_commands(self.commands)
        self.commands = []




class SecurityException(Exception):
    pass

def is_equals(obj1, obj2):
    """determines equality of objects"""
    pass

def parse_uuid(json_uuid):
    """parses a json uuid in the /UUID(...)/ format"""
    return json_uuid[6:len(json_uuid) - 2]

def parse_type(json_type):
    """parses out the type name to return"""
    return json_type[6:len(json_type) - 2]

def parse_date(json_date):
    """parses out the date in the json string and returns a python date object"""
    dateStr = json_date[6:len(json_date) - 2]
    return datetime.fromtimestamp(int(dateStr) / 1000)

def parse_value(value):
    """parses the value from json notation and returns a python version of it"""
    if isinstance(value, str) or isinstance(value, unicode):
        if value.startswith('/UUID('):
            return parse_uuid(value)
        elif value.startswith('/Type('):
            return parse_type(value)
        elif value.startswith('/Date('):
            return parse_date(value)
        return value
    elif isinstance(value, dict):
        block = get_block_store().inflate_block(value)
        if block.type in ['DateObject', 'DateTimeObject']:
            get_block_store().remove_block(block)
            return block.get('date')
        else:
            return block
    elif isinstance(value, list):
        return map(parse_value, value)
    else:
        return value

def isuuid(val):
    """tests whether this is a uuid string"""
    return (isinstance(val, str) or isinstance(val, unicode)) and len(val) == 36 and val[8] == '-' and val[13] == '-' and val[18] == '-' and val[23] == '-'

def get_json_value(value):
    """returns a python value properly formatted for json"""
    if isuuid(value):
        return "/UUID(%s)/" % value
    elif isinstance(value, datetime):
        return "/Date(%i)/" % int(mktime(value.timetuple()) * 1000)
    elif isinstance(value, Block):
        return get_json_value(value.uuid)
    else:
        return value

def test_starter():
    service = SpringRpcService()
    service.authenticate('pete', 'test')
    return service

def main():
    pass

if __name__ == "__main__":
    main()