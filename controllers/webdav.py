#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.

from argeweb import Controller
from plugins.file.models.file_model import FileModel


class Webdav(Controller):
    class Meta:
        Model = FileModel

    class Scaffold:
        display_in_list = ['title', 'path', 'content_type', 'content_length']
        hidden_in_form = ['resource_data']

