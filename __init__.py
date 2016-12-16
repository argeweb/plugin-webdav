#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2015/7/12.
from argeweb import datastore

plugins_helper = {
    'title': u'Webdav',
    'desc': u'UserFile With WebDAV Server',
    'controllers': {
        'user_file': {
            'group': u'使用者檔案',
            'actions': [
                {'action': 'list', 'name': u'使用者檔案'},
                {'action': 'add', 'name': u'新增使用者檔案'},
                {'action': 'edit', 'name': u'編輯使用者檔案'},
                {'action': 'view', 'name': u'檢視使用者檔案'},
                {'action': 'delete', 'name': u'刪除使用者檔案'},
                {'action': 'plugins_check', 'name': u'啟用停用模組'},
            ]
        },
        'user_file_category': {
            'group': u'使用者檔案分類',
            'actions': [
                {'action': 'list', 'name': u'使用者檔案分類'},
                {'action': 'add', 'name': u'新增使用者檔案分類'},
                {'action': 'edit', 'name': u'編輯使用者檔案分類'},
                {'action': 'view', 'name': u'檢視使用者檔案分類'},
                {'action': 'delete', 'name': u'刪除使用者檔案分類'},
            ]
        }
    }
}
