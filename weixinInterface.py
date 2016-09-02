# -*- coding: utf-8 -*-
import hashlib
import web
import lxml
import time
import os


class WeixinInterface:
    def GET(self):
        data = web.input()               # 获取输入参数
        signature=data.signature
        timestamp=data.timestamp
        nonce=data.nonce
        echostr=data.echostr
        token='siratori'                 # 这里改写你在微信公众平台里输入的token
        list=[token, timestamp, nonce]
        list.sort()
        sha1=hashlib.sha1()
        map(sha1.update, list)
        hashcode=sha1.hexdigest()        # sha1加密算法

        #如果是来自微信的请求，则回复echostr
        if hashcode == signature:
            return echostr

    def POST(self):
        str_xml = web.data()             # 获得post来的数据
        xml = etree.fromstring(str_xml)  # 进行XML解析
        content=xml.find('Content').text # 获得用户所输入的内容
        msgType=xml.find('MsgType').text
        fromUser=xml.find('FromUserName').text
        toUser=xml.find('ToUserName').text
