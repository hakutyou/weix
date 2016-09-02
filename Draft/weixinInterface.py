# -*- coding: utf-8 -*-
import hashlib
import web
import lxml
import time
import os
import urllib2
import json
import random
import re
import pylibmc as memcache
from lxml import etree
from math import *

import safeeval

class WeixinInterface:
    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root, 'templates')
        self.render = web.template.render(self.templates_root)
        self.adminlist = ["ovhXRs9PhAtBmCSR9dfiBTcM1TFQ"]
        self.constant()

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
        self.mc = memcache.Client()
        if not self.mc.get(fromUser+'_status'):
            self.mc.set(fromUser+'_status', 'normal')
        mcmode = self.mc.get(fromUser+'_status')

        if msgType == 'event':
            mscontent = xml.find('Event').text
            if mscontent == 'subscribe':
                replyText = u'''ようこそ'''
                return self.render.reply_text(fromUser, toUser, int(time.time()), replyText)
            if mscontent == 'unsubscribe':
                replyText = u'''さようなら'''
                return self.render.reply_text(fromUser, toUser, int(time.time()), replyText)
            return replyxml

        if msgType == 'text':
            content = xml.find('Content').text

            mdcommand = self.command.get(mcmode)
            dividecontent = content.split(' ')

            if dividecontent[0] in mdcommand.keys():
                return self.render.reply_text(fromUser, toUser,
                                              int(time.time()),
                                              mdcommand.get(dividecontent[0])
                                              (fromUser, dividecontent))

            if content == 'm':
                musicList = [
                    [r'http://up.haoduoge.com/mp3/2016-06-20/1466416623.mp3' , 'Reimu', 'Touhou']
                ]
                music = random.choice(musicList)
                musicurl = music[0]
                musictitle = music[1]
                musicdes = music[2]
                return self.render.reply_music(fromUser, toUser,
                                               int(time.time()),
                                               musictitle,
                                               musicdes,
                                               musicurl)

            return self.render.reply_text(fromUser, toUser, int(time.time()),
                    self.command_default.get(mcmode)(fromUser, content))
        return self.render.reply_text(fromUser, toUser, int(time.time()), u'未知信息类型')


    def _MODE(self, fromUser, args):
        '''
        mode: 查询当前Mode
        '''
        return 'Mode: '+self.mc.get(fromUser+'_status')

    def _SETMODE(self, fromUser, args):
        '''
        setmode: 修改当前 Mode
        exit: 将 Mode 设为 Normal
        '''
        if args[0] in self.command.keys():
            self.mc.set(fromUser+'_status', '%s' % (args[0]))
        else:
            self.mc.set(fromUser+'_status', 'normal')
        return self._MODE(fromUser, args)


    def _NORMAL(self, fromUser, command):
        match = re.match(ur'^(weather|天气) (\w+|[\u4e00-\u9fa5]+)', command)
        if match:
            city = match.group(2)
            return self.__WEAT(city.encode('utf-8'))
        return u'输入help查看指令列表'

    def _GETUID(self, fromUser, command):
        return fromUser

    def __WEAT(self, city):
        try:
            city_name = urllib2.quote(city)
            url_str = 'http://api.map.baidu.com/telematics/v3/weather?location={city}&ak={key}&output=json'.format(
            city=city_name,
            key = '31662bc776555612e3639dbca1ad1fd5'
            )
            response = urllib2.urlopen(url_str)
            data_html = response.read()
            json_result = json.loads(data_html)['results'][0]
            str_data = json_result['currentCity'] + ' PM:' + json_result['pm25'] + '\n'
            try:
                 str_data += json_result['index'][0]['des'] + '\n'
            except:
                pass
            for data in json_result['weather_data']:
                str_data += data['date'] + ' ' + data['weather'] + ' '
                str_data += data['wind'] + ' ' + data['temperature'] + '\n'
        except:
            str_data = u'无此城市记录'
        return str_data

    def _HELP(self, fromUser, args):
        '''
        help: 列出帮助文档
        help [command]: 列出相应command的文档
        '''
        str = ''
        if len(args)>1:
            i = 1
            modedict = self.command.get(self.mc.get(fromUser+'_status'))
            while i < len(args):
                if args[i] in modedict.keys():
                    str += modedict.get(args[i]).__doc__ + '\n'
                else:
                    str += args[i] + u'不是可用的命令\n'
                i += 1
        else:
            mode = self.mc.get(fromUser+'_status')
            str = 'Command List: %s' % (self.command.get(mode).keys())
        return str

    def _FOLLOW(self, fromUser, command):
        return command

    def _TRANSLATE(self, fromUser, command):
        word = command.encode('utf-8')
        qword = urllib2.quote(word)
        baseurl = r'http://fanyi.youdao.com/openapi.do?keyfrom=yakusu&key=737954732&type=data&doctype=json&version=1.1&q='
        url = baseurl+qword
        resp = urllib2.urlopen(url)
        yakusu = json.loads(resp.read())
        if yakusu['errorCode'] == 0:
            if 'basic' in yakusu.keys():
                trans = u'%s: %s\n<基本词典>\n%s\n<网络释义>\n%s\n' % (
                        yakusu['query'],
                        '; '.join(yakusu['translation']),
                        '\n'.join(yakusu['basic']['explains']),
                        '; '.join(yakusu['web'][0]['value']))
                trans += u'<比较> '
                for ex in yakusu['web'][1:]:
                    trans += '\n' + ex['key'] + ': ' + "; ".join(ex['value'])
                return trans
            else:
                trans = u'%s:\n基本翻译:%s\n'%(yakusu['query'], ''.join(yakusu['translation']))
                return trans
        elif yakusu['errorCode'] == 20:
            return u'翻译的文本过长'
        elif yakusu['errorCode'] == 30:
            return u'无法进行有效的翻译'
        elif yakusu['errorCode'] == 40:
            return u'不支持的语言类型'
        else:
            return u'您输入的单词%s无法翻译, 请检查拼写' % word

    def _CALC(self, fromUser, command):
        if fromUser in self.adminlist:
            return "%s" % (eval(command))
        return "%s" % (safe_eval(command))

    def constant(self):
        self.command_general = {
            'help': self._HELP,
            'mode': self._MODE
        }

        self.command_normal = self.command_general.copy()
        self.command_follow = self.command_general.copy()
        self.command_translate = self.command_general.copy()
        self.command_calc = self.command_general.copy()

        self.command_normal.update({
            'follow': self._SETMODE,
            'translate': self._SETMODE,
            'calc': self._SETMODE,
            'getid': self._GETUID
        })
        self.command_follow.update({
            'exit': self._SETMODE,
            'normal': self._SETMODE
        })
        self.command_translate.update({
            'exit': self._SETMODE,
            'normal': self._SETMODE
        })
        self.command_calc.update({
            'exit': self._SETMODE,
            'normal': self._SETMODE
        })

        self.command = {
            'normal': self.command_normal,
            'follow': self.command_follow,
            'translate': self.command_translate,
            'calc': self.command_calc
        }

        self.command_default = {
            'normal': self._NORMAL,
            'follow': self._FOLLOW,
            'translate': self._TRANSLATE,
            'calc': self._CALC
        }

class Menu:
    def GET(self):
        appid = 'wx87e706bd1dfecefb'
        token = 'N2wc0Qy5FEZAjEAFjoOHXcvOV_ItIXyzGUJ-XaFcQTGuJH4sbJmlbcRzipuqfWq40qNg_4_Azw2Yk1wznAxPObd1OtC1ABIFOM_7A9DD-mAZEUiACAGLB'
        post='''
 {
   "button":[
   {
      "type":"click",
      "name":"开始",
      "key":"begin"
   },
   {
       "type":"click",
       "name":"结束",
       "key":"end"
   },
   {
      "type":"click",
       "name":"游戏",
       "key":"play"	
   }]
 }'''
        url = 'https://api.weixin.qq.com/cgi-bin/menu/create?access_token='+token
        req = urllib2.Request(url, post)
        response = urllib2.urlopen(req)
        return response

class DMenu:
    def GET(self):
        appid = 'wx87e706bd1dfecefb'
        token = 'N2wc0Qy5FEZAjEAFjoOHXcvOV_ItIXyzGUJ-XaFcQTGuJH4sbJmlbcRzipuqfWq40qNg_4_Azw2Yk1wznAxPObd1OtC1ABIFOM_7A9DD-mAZEUiACAGLB'
        url = 'https://api.weixin.qq.com/cgi-bin/menu/delete?access_token='+token
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        return response

