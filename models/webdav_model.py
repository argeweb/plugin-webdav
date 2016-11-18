#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.

from argeweb import BasicModel
from argeweb import Fields
from urllib import pathname2url
from google.appengine.ext import ndb
from xml.etree import ElementTree as ET
import mimetypes
import logging
import os
from webdav_self_referential_model import WebdavModel as selfReferentialModel


class WebdavResourceData(ndb.Model):
    name = ndb.StringProperty()
    title = ndb.StringProperty()
    blob = ndb.BlobProperty()


class WebdavModel(BasicModel):
    name = Fields.StringProperty(verbose_name=u"名稱")
    title = Fields.StringProperty(verbose_name=u"標題")
    path = Fields.StringProperty(verbose_name=u"檔案路徑")
    content_length = Fields.IntegerProperty(verbose_name=u"檔案類型")
    content_type = Fields.StringProperty(verbose_name=u"檔案大小")
    parent_resource = Fields.CategoryProperty(kind=selfReferentialModel, verbose_name=u"所屬目錄")
    is_collection = Fields.BooleanProperty(default=False, verbose_name=u"是否為目錄")
    created = Fields.DateTimeProperty(auto_now_add=True)
    modified = Fields.DateTimeProperty(auto_now=True)
    content_language = Fields.StringProperty()
    etag = Fields.StringProperty(verbose_name=u"etag")
    resource_data = Fields.CategoryProperty(kind=WebdavResourceData, verbose_name=u"檔案實體")

    @property
    def children(self):
        if self.is_collection:
            logging.info(self.key)
            return WebdavModel().all().filter(WebdavModel.parent_resource == self.key)
        else:
            return []

    @property
    def display_name(self):
        return os.path.basename("%s" % self.path)

    @property
    def path_as_url(self):
        return pathname2url(self.path)

    @property
    def content_type_or_default(self):
        if self.is_collection:
            return 'httpd/unix-directory'
        else:
            mimetype = mimetypes.guess_type(self.path,strict=False)[0]
            return mimetype if mimetype else 'application/octet-stream'

    @classmethod
    def root(cls):
        root = cls.all().filter(cls.parent_resource == None).get()
        if not root:
            root = cls(path='', is_collection=True)
            root.put()
        return root

    @classmethod
    def get_by_path(cls, path=None):
        return cls.all().filter(cls.path == path).get() if path else cls.root()

    @classmethod
    def exists_with_path(cls, path="", is_collection=None):
        query = cls.all().filter(cls.path == path)
        if is_collection is not None:
            query = query.filter(cls.is_collection == True)
        return query.get(keys_only=True) is not None

    def move_to_path(self, destination_path):
        """Moves this resource and all its children (if applicable) to a new path.
           Assumes that the new path is free and clear."""

        if self.is_collection:
            for child in self.children:
                child_name = os.path.basename(child.path)
                child_path = os.path.join(destination_path,child_name)
                child.move_to_path(child_path)

        self.path = destination_path
        self.put()

    def put(self):
        # workaround for general non-solveable issue of no UNIQUE constraint concept in app engine datastore.
        # anytime we save, we look for the possibility of other duplicate Resources with the same path and delete them.
        for duped_resource in WebdavModel.all().filter(WebdavModel.path == self.path):
            if self.key().id() != duped_resource.key().id():
                logging.info("Deleting duplicate resource %s with path %s." % (duped_resource,duped_resource.path))
                duped_resource.delete()
        self.name = self.display_name
        self.title = self.name
        super(WebdavModel, self).put()

    def delete(self):
        """Override delete to delete our associated ResourceData entity automatically."""
        if self.resource_data:
            n = self.resource_data.get()
            if n:
                n.key.delete()
        self.key.delete()

    def delete_recursive(self):
        """Deletes this entity plus all of its children and other descendants."""
        if self.is_collection:
            for child in self.children:
                child.delete_recursive()
        self.delete()

    def export_response(self, href=None):
        datetime_format = '%Y-%m-%dT%H:%M:%SZ'

        response = ET.Element('D:response',{'xmlns:D':'DAV:'})
        ET.SubElement(response, 'D:href').text = href
        propstat = ET.SubElement(response,'D:propstat')
        prop = ET.SubElement(propstat,'D:prop')

        if self.created:
            ET.SubElement(prop, 'D:creationdate').text = self.created.strftime(datetime_format)

        ET.SubElement(prop, 'D:displayname').text = self.display_name

        if self.content_language:
            ET.SubElement(prop, 'D:getcontentlanguage').text = str(self.content_language)

        ET.SubElement(prop, 'D:getcontentlength').text = str(self.content_length)
        ET.SubElement(prop, 'D:getcontenttype').text = str(self.content_type_or_default)

        if self.modified:
            ET.SubElement(prop, 'D:getlastmodified').text = self.modified.strftime(datetime_format)

        resourcetype = ET.SubElement(prop,'D:resourcetype')

        if self.is_collection:
            ET.SubElement(resourcetype, 'D:collection')

        ET.SubElement(propstat,'D:status').text = "HTTP/1.1 200 OK"
        return response





