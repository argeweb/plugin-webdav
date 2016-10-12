#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.

from argeweb import Controller, scaffold, route_menu, route_with
from argeweb.components.pagination import Pagination
from argeweb.components.search import Search
from .. import plugins_helper


class UserFile(Controller):
    class Meta:
        components = (scaffold.Scaffolding, Pagination, Search)
        pagination_actions = ("list",)
        pagination_limit = 50

    class Scaffold:
        helper = plugins_helper
        display_properties_in_list = ("path", "etag", "parent_resource", "display_name", "content_type", "content_length", "data")

    @route_menu(list_name=u"backend", text=u"Webdav", sort=9801, icon="files-o", group=u"檔案管理")
    @route_with('/admin/webdav/list')
    def admin_list(self):
        return scaffold.list(self)

    @route_with('/admin/webdav/plugins_check')
    def admin_plugins_check(self):
        self.meta.change_view('jsonp')
        self.context['data'] = {
            'status': "enable"
        }