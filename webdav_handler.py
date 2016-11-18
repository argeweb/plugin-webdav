#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2016/8/27

from google.appengine.ext.webapp.util import run_wsgi_app
import webapp2
from urllib import url2pathname, pathname2url
from urlparse import urlparse
from xml.etree import ElementTree as ET
import logging
import os
from plugins.file.models.file_model import FileModel as Resource, FileDataModel
from argeweb.core.settings import get_host_information_item
from google.appengine.api import namespace_manager




class WebDAVHandler(webapp2.RequestHandler):
    """
COPY。用於複製資源。可以使用 Depth: 標頭來移動集合，而使用 Destination: 標頭來指定目標。如果適用，COPY 方法也使用 Overwrite: 標頭。
MOVE。用於移動資源。可以使用 Depth: 標頭來移動集合，而使用 Destination: 標頭來指定目標。如果適用，MOVE 方法也使用 Overwrite: 標頭。
MKCOL。用於建立新集合。此方法用來避免使 PUT 方法超載。
PROPPATCH。用於設定、變更或刪除單一資源的特性。
PROPFIND。用於擷取一個或多個資源中的一個或多個特性。當用戶端向伺服器提交對某個集合的 PROPFIND 請求時，該請求可能會包含一個值為 0、1 或 infinity 的 Depth: 標頭。
0。指定將會擷取指定 URI 位置的集合特性。
1。指定將會擷取集合特性以及直接位於指定 URI 之下的資源特性。
infinity。指定將會擷取集合及其包含的全部成員 URI 的特性。請注意，由於深度為無窮大的請求需要遍歷整個集合，因而會顯著增加伺服器的負擔。
LOCK。為資源增加鎖定。使用 Lock-Token: 標頭。
UNLOCK。移除資源的鎖定。使用 Lock-Token: 標頭。
    """
    __status__ = {
        "201": "Created",
        "204": "No Content",
        "207": "Multi-Status",
        "403": "Forbidden",
        "404": "Not Found",
        "405": "Method Not Allowed",
        "409": "Conflict",
        "412": "Precondition Failed",
    }

    def set_status(self, code):
        code = str(code)
        if code not in self.__status__:
            code = "404"
        return self.response.set_status(int(code), self.__status__[code])

    def initialize(self, request, response):
        self.host, self.namespace, self.theme = get_host_information_item()
        namespace_manager.set_namespace(self.namespace)
        super(WebDAVHandler, self).initialize(request, response)
        self.request_path = "%s" % self.url_to_path(self.request.path) if request else ""

    def set_prefix(self, prefix):
        # normalize
        self._prefix = '/%s/' % prefix.strip('/') if prefix else '/'

    def url_to_path(self, path):
        """Accepts a relative url string and converts it to our internal relative path (minux prefix) used in our Resource entities."""
        return url2pathname( # decode '%20's and such
            path[len(self._prefix):] # chop off prefix
        ).strip('/')

    def options(self):
        self.response.headers['Allow'] = 'GET, PUT, DELETE, MKCOL, OPTIONS, COPY, MOVE, PROPFIND, PROPPATCH, LOCK, UNLOCK, HEAD'
        self.response.headers['Content-Type'] = 'httpd/unix-directory'

    def proppatch(self):
        path = self.request_path
        self.propfind_resource(Resource.get_by_path(path))

    def propfind(self):
        path = self.request_path
        self.propfind_resource(Resource.get_by_path(path))

    def propfind_resource(self, resource, children=None):
        depth = self.request.headers.get('depth', '0')

        if depth != '0' and depth != '1':
            return self.set_status(403)

        if not resource:
            return self.set_status(404)

        root = ET.Element('multistatus',{'xmlns':'DAV:'})
        root.append(resource.export_response(href=self.request.path)) # first response's href contains exactly what you asked for (relative path)
        if resource.is_collection and depth == '1':
            if children is None: # you can give us children if you don't want us to ask the resource
                children = resource.children
            for child in children:
                abs_path = None
                path = self._prefix + child.path
                try:
                    abs_path = pathname2url(path.encode('utf-8'))
                except KeyError:
                    try:
                        abs_path = pathname2url(path)
                    except:
                        pass
                except:
                    pass
                if abs_path is not None:
                    root.append(child.export_response(href=abs_path))

        self.response.headers['Content-Type'] = 'text/xml; charset="utf-8"'
        self.set_status(207)
        ET.ElementTree(root).write(self.response.out, encoding='utf-8')

    def mkcol(self):
        """Creates a subdirectory, given an absolute path."""
        path = self.request_path
        parent_path = os.path.dirname(path)

        # check for duplicate
        if Resource.exists_with_path(path):
            return self.set_status(405)

        # fetch parent
        if parent_path:
            parent = Resource.get_by_path(parent_path)
            if not parent:
                return self.set_status(409) # must create parent folder first
        else:
            parent = Resource.root()

        logging.info("Creating dir at %s" % path)
        collection = Resource()
        collection.path = path
        collection.parent_resource = parent.key
        collection.is_collection = True
        collection.put()

        self.set_status(201)

    def delete(self):
        """Deletes a resource at a url. If it's a collection, it must be empty."""
        path = self.request_path
        resource = Resource.get_by_path(path)

        if not resource:
            return self.set_status(404)

        resource.delete_recursive()

    def move(self):
        """Moves a resource from one path to another."""
        path = self.request_path
        resource = Resource.get_by_path(path)
        logging.info(path, resource)

        if not resource:
            return self.set_status(404)

        overwrite = self.request.headers.get('Overwrite', 'T')
        destination = self.request.headers['Destination'] # exception if not present

        destination_path = self.url_to_path(urlparse(destination).path)
        parent_path = os.path.dirname(destination_path)

        if path == destination_path:
            return self.set_status(403)

        # anything at this path already?
        existing_resource = Resource.get_by_path(destination_path)

        if existing_resource:
            if overwrite == 'T':
                existing_resource.delete_recursive()
            else:
                return self.set_status(412)

        # fetch parent
        if parent_path:
            parent = Resource.get_by_path(parent_path)
            if not parent or not parent.is_collection:
                return self.set_status(409) # must create parent folder first
        else:
            parent = Resource.root()

        resource.parent_resource = parent # reparent this node
        resource.move_to_path(destination_path)

        self.set_status(204 if existing_resource else 201)

    def put(self):
        """Uploads a file."""
        path = self.request_path
        parent_path = os.path.dirname(path)

        # anything at this path already?
        existing_resource = Resource.get_by_path(path)

        if existing_resource:
            existing_resource.delete_recursive()

        # fetch parent
        logging.info("path : %s" % path)
        logging.info("parent_path : %s" % parent_path)
        if parent_path:
            parent = Resource.get_by_path(parent_path)
            logging.info("parent : %s" % parent)
            if not parent or not parent.is_collection:
                return self.set_status(409) # must create parent folder first
        else:
            parent = Resource.root()

        logging.info("Creating resource at %s" % path)
        data = FileDataModel(blob=self.request.body)
        data.put()

        resource = Resource()
        resource.path = path
        resource.parent_resource = parent.key
        resource.resource_data = data.key
        resource.content_length = len(self.request.body)
        resource.put()

        self.set_status(201)

    def head(self):
        """Gets information about a resource sans the data itself."""
        self.get() # app engine will chop off the body for us, this is the only way to make Google send a Content-Length header without the actual body being that length.

    def get(self):
        """Downloads a file."""
        path = self.request_path
        resource = Resource.get_by_path(path)

        if not resource:
            return self.set_status(404)

        if resource.is_collection:
            template_values = {
                'path': path,
                'prefix': self._prefix,
                'resources': [child for child in resource.children if not child.display_name.startswith('.')]
            }
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'collection.html')
            self.response.out.write((template_path, template_values))
        else:
            # deliver the file data
            self.response.headers['Content-Type'] = resource.content_type_or_default
            self.response.out.write(resource.resource_data.get().blob)

    def lock(self):
        """Locks a resource. We don't actually support this so we'll just send the expected 'success!' response."""
        depth = self.request.headers.get('depth', '0')
        timeout = self.request.headers.get('Timeout',None)

        root = ET.Element('prop',{'xmlns':'DAV:'})
        lockdiscovery = ET.SubElement(root, 'lockdiscovery')
        activelock = ET.SubElement(lockdiscovery, 'activelock')
        ET.SubElement(activelock, 'lockscope')
        ET.SubElement(activelock, 'locktype')
        ET.SubElement(activelock, 'depth').text = depth
        ET.SubElement(activelock, 'owner')
        ET.SubElement(activelock, 'timeout').text = timeout

        locktoken = ET.SubElement(activelock, 'locktoken')
        ET.SubElement(locktoken, 'href').text = 'opaquelocktoken:' # copying box.net

        self.response.headers['Content-Type'] = 'text/xml; charset="utf-8"'
        ET.ElementTree(root).write(self.response.out, encoding='utf-8')

    def unlock(self):
        """We don't actually support locking so we'll just pretent it worked, OK?"""
        self.set_status(204)

