#!/usr/bin/python
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
from lxml import etree
import pylibmc as memcache

from math import *
import safeeval

class Reply:

    def __init__(self):
	self.app_root = os.path.dirname(__file__)
	self.templates_root = os.path.join(self.app_root, 'templates')
	self.render = web.template.render(self.templates_root)

	appid = 'wx695f2c976647c87d'
	secret = '64da6bda790f66ddddfabea9994fa672'
	#appid = 'wx87e706bd1dfecefb'
	#secret= 'b25d25ec3390e70980553b2ad29a1a48'
	url_get_token='https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid='+appid+'&secret='+secret
	response_get_token = urllib2.urlopen(url_get_token)
	html_get_token = response_get_token.read()
	access_token = json.loads(html_get_token)['access_token']
	self.access_token = access_token

	# 初期化
        self.adminlist = ['ovhXRs9PhAtBmCSR9dfiBTcM1TFQ']
	self.command_general = {
            'h': self._HELP,
            'm': self._MODE,
            'q': self._SETMODE,
	    'w': self._MODE
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

    def GET(self):
	data = web.input()
	signature = data.signature
	timestamp = data.timestamp
	nonce = data.nonce
	echostr = data.echostr
	token = 'sirat'
	list = [token,timestamp,nonce]
	list.sort()
	sha1 = hashlib.sha1()
	map(sha1.update,list)
	hashcode = sha1.hexdigest()
	if hashcode == signature:
	    return echostr

    def POST(self):
	str_xml = web.data()
	xml = etree.fromstring(str_xml)
	msgType = xml.find('MsgType').text
	fromUser = xml.find('FromUserName').text
	toUser = xml.find('ToUserName').text
	#createTime = xml.find('CreateTime').text
        self.mc = memcache.Client()
        if not self.mc.get(fromUser+'_status'):
            self.mc.set(fromUser+'_status', 'normal')
        mcmode = self.mc.get(fromUser+'_status')


	if msgType == 'text': # 接收到文本信息
	    content = xml.find('Content').text
            mdcommand = self.command.get(mcmode)
            dividecontent = content.split(' ')
            if dividecontent[0] in mdcommand.keys():
		reply = mdcommand.get(dividecontent[0])(fromUser, dividecontent)
	    elif content == 'm':
		musicList = [
		    [r'http://up.haoduoge.com/mp3/2016-06-20/1466416623.mp3' ,
			'Reimu', 'Touhou'] ]
		music = random.choice(musicList)
		musicurl = music[0]
		musictitle = music[1]
		musicdes = music[2]
		return self.render.reply_music(fromUser, toUser,
			int(time.time()), musictitle, musicdes, musicurl)
	    else:
		reply = self.command_default.get(mcmode)(fromUser, content)
	elif msgType == 'image':
	    reply = '图片消息'
	elif msgType == 'voice':
	    reply = '语音消息'
	elif msgType == 'video':
	    reply = '视频消息'
	elif msgType == 'location':
	    reply = '地理消息'
	elif msgType == 'link':
	    reply = '链接消息'
	elif msgType == 'event':
	    event = xml.find('Event').text
            if event == 'subscribe': # 关注回复
	        reply = 'ようこそ'
	    elif event == 'unsubscribe': # 取消关注
		reply = 'まだ'
            elif event == 'CLICK':
	        key = xml.find('EventKey').text
                if key == 'weather':
		    self.mc.set(fromUser+'_status', 'normal')
                    reply = '进入普通模式，回复"天气 [地点]"查询天气'
                elif key == 'translate':
		    self.mc.set(fromUser+'_status', key)
                    reply = '已进入翻译模式, 回复单词查看翻译'
                elif key == 'calc':
		    self.mc.set(fromUser+'_status', key)
                    reply = '已进入Calc模式, 回复语句进行Calc'
                elif key == 'code':
		    return self.code(fromUser, toUser)
                else:
                    reply = '未知按钮' + key
            else:
                reply='未知事件' + event
	else:
	    reply='未知类型'
        return self.render.reply_text(fromUser, toUser, int(time.time()), reply)

    def code(self, fromUser, toUser): # 发送二维码
	return self.render.reply_pictext(fromUser, toUser, int(time.time()), '二维码', '点击查看大图', 'http://mmbiz.qpic.cn/mmbiz_jpg/JCr7auYqwp82b1V5dx2ZEZlHwfx0F5ZW3u2nN3tOY6K2eHD8sM62KWviaKvgeZlLgzKY9L9VSfyjdGIBvRCTDcg/0','http://mmbiz.qpic.cn/mmbiz_jpg/JCr7auYqwp82b1V5dx2ZEZlHwfx0F5ZW3u2nN3tOY6K2eHD8sM62KWviaKvgeZlLgzKY9L9VSfyjdGIBvRCTDcg/0')

    def _MODE(self, fromUser, args):
        '''''
        mode: 查询当前模式
	'''
        return 'Mode: '+self.mc.get(fromUser+'_status')

    def _SETMODE(self, fromUser, args):
        '''''
        setmode: 修改当前模式
        q: 将 Mode 设为 Normal
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
        return '回复h查看指令列表'

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
            str_data = '无此城市记录'
        return str_data

    def _HELP(self, fromUser, args):
        '''''
        h: 列出帮助文档
        h [命令]: 列出相应命令的文档
	'''
        str = ''
        if len(args)>1:
            i = 1
            modedict = self.command.get(self.mc.get(fromUser+'_status'))
            while i < len(args):
                if args[i] in modedict.keys():
                    str += modedict.get(args[i]).__doc__
                else:
                    str += args[i] + '不是可用的命令'
                i += 1
        else:
            mode = self.mc.get(fromUser+'_status')
            str = '可用的指令: %s\n回复h [command]查看详情' % (self.command.get(mode).keys())
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
                    trans += '\n' + ex['key'] + ': ' + '; '.join(ex['value'])
                return trans
            else:
                trans = u'%s:\n基本翻译:%s\n'%(yakusu['query'], ''.join(yakusu['translation']))
                return trans
        elif yakusu['errorCode'] == 20:
            return '翻译的文本过长'
        elif yakusu['errorCode'] == 30:
            return '无法进行有效的翻译'
        elif yakusu['errorCode'] == 40:
            return '不支持的语言类型'
        else:
            return '输入的单词%s无法翻译, 请检查拼写' % word

    def _CALC(self, fromUser, command):
        if fromUser in self.adminlist:
            return '%s' % (eval(command))
        return '%s' % (eval(command))
        return '%s' % (safe_eval(command))
