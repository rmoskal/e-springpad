from google.appengine.api import taskqueue
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import collection_cache
import os
from google.appengine.ext.webapp import template
import oauth2
import oauth
import logging
from gaesessions import get_current_session
import evernotebookparser
import springpad


APPLICATION_KEY = "d21f1c131fb14c769f54872d0d5a8dc6"
APPLICATION_SECRET = "a65db20e8f8844b282a133026a5c639d"

class MainHandler(webapp.RequestHandler):

    def get(self, mode=""):
        templateName = 'templates/index.html'
        data = {}

        session = get_current_session()
        callback_url = "%s/work" % self.request.host_url
        client = oauth2.SpringpadClient(APPLICATION_KEY, APPLICATION_SECRET,
        callback_url)
        #session.clear()
        if session.has_key("token"):
            token = session.get("token")
            secret = session.get("secret")
            results = client._lookup_user_info(token,secret)
            data = results
            session["userInfo"] = results
            templateName = 'templates/worker.html'
            upload_url = blobstore.create_upload_url('/upload')
            data['upload_url'] = upload_url
            if self.request.get('workbook'):
               data['total'] = '<span class="note alert">You uploaded %s bytes. Your items will be copied into a new springpad notebook named "%s". Feel free to upload another while you wait.</span>' % (self.request.get('size'),self.request.get('workbook'))


        path = os.path.join(os.path.dirname(__file__),templateName)
        self.response.out.write(template.render(path,data))

        
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):

        session = get_current_session()
        workbook = self.request.get("workbook")
        upload_files = self.get_uploads('content')
        blob_info = upload_files[0]

        token = session.get("token")
        secret = session.get("secret")
        userInfo = session["userInfo"]

        service = springpad.SpringRpcService()
        service.fetcher = springpad.OAuthFetcher(APPLICATION_KEY, APPLICATION_SECRET,access_token=oauth.OAuthToken(token,secret))
        service.set_user_context(userInfo['username'], userInfo['uuid'])

        mutator = service.get_mutator()
        notebook = mutator.create("Workbook")
        mutator.set(notebook, 'name', workbook)
        mutator.commit()

        taskqueue.add(url='/queue', params={'token': token,
                                            'secret': secret,
                                            'username':userInfo['username'],
                                            'uuid':userInfo['uuid'],
                                            'content':blob_info.key(),
                                             'workbook' :notebook.uuid
                                            })
        self.redirect('/?workbook=%s&size=%s'%(workbook, blob_info.size))
        

class LoginHandler(webapp.RequestHandler):
    def get(self):

        callback_url = "%s/work" % self.request.host_url
        client = oauth2.SpringpadClient(APPLICATION_KEY, APPLICATION_SECRET,
        callback_url)
        return self.redirect(client.get_authorization_url())


class ValidationHandler(webapp.RequestHandler):
    def get(self):
        callback_url = "%s/work" % self.request.host_url
        client = oauth2.SpringpadClient(APPLICATION_KEY, APPLICATION_SECRET,
        callback_url)
        session = get_current_session()
        auth_token = self.request.get("oauth_token")
        results = client.get_user_info(auth_token)
        session["token"] = results["token"]
        session["secret"] = results["secret"]
        return self.redirect("/")

class ImportWorker(webapp.RequestHandler):
    def post(self):
        workbook = self.request.get("workbook")
        token =  self.request.get("token")
        secret =  self.request.get("secret")
        username = self.request.get("username")
        uuid = self.request.get("uuid")
        blobkey = self.request.get("content")
        try:
            service = springpad.SpringRpcService()
            service.fetcher = springpad.OAuthFetcher(APPLICATION_KEY, APPLICATION_SECRET,access_token=oauth.OAuthToken(token,secret))
            service.set_user_context(username, uuid)
            mutator = service.get_mutator()

            blob_reader = blobstore.BlobReader(blobkey)
            parser = evernotebookparser.NotebookParser2(blob_reader)
            parser.get_items(lambda x: createItem(mutator,workbook,x))
            logging.info("Serviced a customer")
            blob_reader.close()
            blobstore.delete(blobkey)
        except Exception,e:
            logging.exception("-------%s"%e.message)
            try:
                blobstore.delete(blobkey)
            except :
                pass
    def handle_exception(self,exception, debug_mode):
        logging.exception("-------%s"%exception.message)
        self.set_status(200)





def createItem(mutator,workbook, item):
    if not item:
        return

    logging.info("Creating an item")
    if "url" in item:
        note = mutator.create("Bookmark")
        mutator.set(note,"url", item['url'])
    else:
        note = mutator.create("Note")
        mutator.set(note, 'rich', True)

    mutator.set(note, 'name', item['title'])
    mutator.set(note, 'tags', item['tags'])
    mutator.set(note,"text", item['content'])
    mutator.set(note, 'workbooks', [workbook,])

    mutator.commit()


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/work', ValidationHandler),
                                          ('/login', LoginHandler),
                                          ('/queue', ImportWorker),
                                          ('/upload', UploadHandler),],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
