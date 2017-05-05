#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created with YooLiang Technology (侑良科技).
# Author: Qi-Liang Wen (温啓良）
# Web: http://www.yooliang.com/
# Date: 2017/01/07.

plugins_helper = {
    'title': u'Webdav',
    'desc': u'UserFile With WebDAV Server',
    'controllers': {
        'webdav': {
            'group': u'Webdav',
            'actions': [
                {'action': 'list', 'name': u'Webdav'},
                {'action': 'add', 'name': u'新增使用者檔案'},
                {'action': 'edit', 'name': u'編輯使用者檔案'},
                {'action': 'view', 'name': u'檢視使用者檔案'},
                {'action': 'delete', 'name': u'刪除使用者檔案'},
                {'action': 'plugins_check', 'name': u'啟用停用模組'},
            ]
        }
    }
}
