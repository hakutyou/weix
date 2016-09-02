# coding: utf-8
import os

import sae
import web
import pylibmc
import sys
sys.modules['memcache'] = pylibmc

from weixinInterface import WeixinInterface

urls = (
'/weixin','WeixinInterface'
'/create', 'Menu'
'/del', 'Dmenu'
)

app_root = os.path.dirname(__file__)
templates_root = os.path.join(app_root, 'templates')
render = web.template.render(templates_root)

app = web.application(urls, globals()).wsgifunc()
application = sae.create_wsgi_app(app)
