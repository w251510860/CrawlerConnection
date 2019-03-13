import http.cookiejar as cj
import time
import multiprocessing
import xml.dom.minidom
import requests
import arrow
import re
import logging
from utils import send_warning_email
from WX.get_export_key import get_export_key
from WX.index_data import get_index_data

headers = {
    'Origin': 'https://WX.qq.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,pt;q=0.6,fr;q=0.5,und;q=0.4,cy;q=0.3,zh-TW;q=0.2,de;q=0.1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://WX.qq.com/?&lang=zh_CN',
    'Connection': 'keep-alive',
    'Range': 'bytes=0-'
}

qrcode_params = (
    ('appid', 'wx782c26e4c19acffb'),
    ('redirect_uri', 'https://WX.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage'),
    ('fun', 'new'),
    ('lang', 'zh_CN'),
    ('_', str(arrow.utcnow().timestamp * 1000 + 220)),
)


class WX(object):
    uuid = ''
    is_login = False
    redirect_uri = ''
    base_uri = ''
    s_key = ''
    sid = ''
    uin = ''
    pass_ticket = ''
    sync_key = ''
    wx_url = ''
    webwx_data_ticket = ''
    real_url = ''
    cookies = {}
    export_key = ''
    session = requests.session()
    device_id = 'e040629688153135'
    ticket = ''
    base_request = {}

    def __init__(self):
        self.listen_process = None

    def request_qrcode_uuid(self):
        self.session.cookies = cj.LWPCookieJar()
        self.session.get('https://WX.qq.com/?&lang=zh_CN')
        qrcode_file = self.session.get('https://login.WX.qq.com/jslogin', params=qrcode_params).text
        self.uuid = qrcode_file.split('"')[1]
        return self.uuid

    def get_qrcode_url(self):
        # send_warning_email(f'微信账号异常退出，请扫码重新恢复登录: <p>https://login.weixin.qq.com/qrcode/{self.uuid}</p>')
        print(f'https://login.weixin.qq.com/qrcode/{self.uuid}')
        return f'https://login.weixin.qq.com/qrcode/{self.uuid}'

    @property
    def direct_uri(self):
        return f'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid={self.uuid}&_={int(time.time())}'

    def wait_login(self):
        for i in range(8):
            data = requests.get(self.direct_uri).text
            pm = re.search(r"window.code=(\d+);", data)
            code = pm.group(1)
            if code == '200':
                pm = re.search(r'window.redirect_uri="(\S+?)";', data)
                r_uri = pm.group(1) + '&fun=new'
                self.redirect_uri = r_uri
                self.base_uri = r_uri[:r_uri.rfind('/')]
                self.is_login = True
                ticket = re.findall('.*ticket=(.*)&uuid.*', r_uri)
                if ticket:
                    self.ticket = ticket
                break
            elif code == '408':
                logging.info('[登陆超时] \n')
            else:
                logging.info('[登陆异常] \n')
            time.sleep(15)

    def login(self):
        if self.is_login:
            return
        while True:
            time.sleep(10)
            self.request_qrcode_uuid()
            qrcode_url = self.get_qrcode_url()
            logging.info(f'qrcode_url - > {qrcode_url}')
            self.wait_login()
            if self.is_login:
                break
        return True

    def request_validator_params(self):
        params = (
            ('ticket', self.ticket),
            ('uuid', self.uuid),
            ('lang', ['zh_CN', 'zh_CN']),
            ('scan', arrow.utcnow().timestamp),
            ('fun', 'new'),
            ('version', 'v2'),
        )
        data = requests.get('https://WX.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage', headers=headers,
                            params=params, cookies={}).text
        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement
        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.s_key = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.sid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.uin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data
        if '' in (self.s_key, self.sid, self.uin, self.pass_ticket):
            logging.info('请求校验参数为空')
        self.base_request = {
            'Uin': int(self.uin),
            'Sid': self.sid,
            'Skey': self.s_key,
            'DeviceID': self.device_id,
        }

    def login_url(self):
        time.sleep(20)
        params = {
            ('loginicon', 'true'),
            ('uuid', self.uuid),
            ('tip', '0'),
            ('r', '479648455'),
            ('_', str(arrow.utcnow().timestamp * 1000 + 220)),
        }
        response = self.session.get('https://WX.qq.com/cgi-bin/mmwebwx-bin/login', params=params)
        self.wx_url = response.text.split('"')[1]

    def init_wx(self):
        params = (
            ('r', '117680852'),
            ('lang', 'zh_CN'),
            ('pass_ticket', self.pass_ticket),
        )
        data = '{"BaseRequest":{"Uin":"%s","Sid":"%s","Skey":"%s","DeviceID":"%s"}}' % (self.uin, self.sid, self.s_key, self.device_id)
        response = requests.post('https://WX.qq.com/cgi-bin/mmwebwx-bin/webwxinit', headers=headers, params=params,
                                 cookies={}, data=data)
        sync_key = response.json().get('SyncKey')
        self.sync_key = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in sync_key['List']])

    def parse_session(self):
        self.session.get(self.wx_url)
        for i in self.session.cookies:
            if i.name == 'webwx_data_ticket':
                self.webwx_data_ticket = i.value
        url = f'https://WX.qq.com/cgi-bin/mmwebwx-bin/webwxcheckurl?requrl=https://search.weixin.qq.com/cgi-bin/searchweb/clientjump?tag=wxindex&skey={self.s_key}&deviceid={self.device_id}&pass_ticket={self.pass_ticket}&opcode=2&scene=1&username=@d7ee685fcf1776a69b5ab0f37aa79fa472fccf5a1d6280ee1c6b2764d4f5e696'
        self.real_url = self.session.get(url).url

    def get_export_key_with_cookies(self):
        export_key, cookie = get_export_key(self.real_url)
        if not export_key:
            logging.info('无法获取export key数据')
            return {}
        cookie.update({'webwx_data_ticket': self.webwx_data_ticket})
        self.cookies = cookie
        self.export_key = export_key

    def get_wx_index(self):
        if not self.cookies:
            logging.info('无法获取cookies数据')
            return
        index = get_index_data(self.cookies)
        if not index:
            logging.info('无法获取指数数据')
            return
        return index

    def get_index(self):
        try:
            if not self.is_login:
                self.login()
                self.login_url()
                self.parse_session()
            self.get_export_key_with_cookies()
            wx_index = self.get_wx_index()
            self.request_validator_params()
            self.listen_process = multiprocessing.Process(target=self.listen_wx_active)
            self.listen_process.start()
            return wx_index
        except Exception as e:
            send_warning_email(f'账号异常退出: <p>{e}</p>')
            return None

    def listen_wx_active(self):
        while True:
            self.init_wx()
            if not self.sync_key:
                logging.info('手机微信异常退出')
                self.is_login = False
                break
            time.sleep(20)
