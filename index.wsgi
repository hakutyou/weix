#!/usr/bin/python
# coding: utf-8

import os

import sae
import web

import urllib2
import json

import pylibmc
import sys

sys.modules['memcache'] = pylibmc

from reply import Reply
urls = (
    '/', 'Reply'
)

appid = "wx695f2c976647c87d"
secret = "64da6bda790f66ddddfabea9994fa672"
#appid = "wx87e706bd1dfecefb"
#secret= "b25d25ec3390e70980553b2ad29a1a48"

url_get_token='https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid='+appid+'&secret='+secret
response_get_token = urllib2.urlopen(url_get_token)
html_get_token = response_get_token.read()
access_token = json.loads(html_get_token)['access_token']

url = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s" % access_token
data = {
    "button":[
        {
            "name":"功能",
            "sub_button":[
                {"type":"click",
		 "name":"天气",
                 "key" :"weather"
                },
		{"type":"click",
		 "name":"翻译",
		 "key" :"translate"
		},
		{"type":"click",
		 "name":"计算器",
		 "key" :"calc"
		}]
	},
        {
            "name":"关于",
            "sub_button":[
                {"type":"click",
                 "name":"获取二维码",
                 "key" :"code"
                },
                {"type":"view",
                 "name":"主页",
                 "url" :"kelifrisk.github.io/wap.html"
                }]
        },
    ]
}
#data = json.loads(data)
#data = urllib.urlencode(data)
req = urllib2.Request(url)
req.add_header('Content-Type', 'application/json')
req.add_header('encoding', 'utf-8')
response = urllib2.urlopen(req, json.dumps(data,ensure_ascii=False))
result = response.read()
print result

app_root = os.path.dirname(__file__)
templates_root = os.path.join(app_root, 'templates')
render = web.template.render(templates_root)

app = web.application(urls, globals()).wsgifunc()
application = sae.create_wsgi_app(app)
