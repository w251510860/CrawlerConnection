import re
import time
from random import randint
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sys import platform

from config import EXECUTABLE_PATH, CHROME_PATH

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument('disable-infobars')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('no-sandbox')
caps = DesiredCapabilities.CHROME
if not caps:
    raise Exception('请安装并配置chrome handless...')
caps['loggingPrefs'] = {'performance': 'ALL'}
if platform == "linux" or platform == "linux2":
    if not EXECUTABLE_PATH:
        raise Exception('请安装并配置EXECUTABLE_PATH...')
    chrome_options.binary_location = CHROME_PATH
    driver = webdriver.Chrome(EXECUTABLE_PATH, desired_capabilities=caps, chrome_options=chrome_options)
elif platform == "darwin":
    driver = webdriver.Chrome(desired_capabilities=caps)
else:
    raise Exception('暂不支持os x及linux以外的其他操作系统...')


def get_export_key(login_url):
    driver.get(login_url)
    time.sleep(randint(5, 10))
    real_url = driver.current_url
    export_key = re.findall('.*&exportkey=(.*)&.*', real_url)
    if not export_key:
        driver.close()
        return ''
    index_cookie = {
        'webwx_data_ticket': '',
        'mmsearch_user_key': '',
        'pass_ticket': '',
        'pgv_pvi': '',
        'pgv_si': ''
    }
    for cookie in driver.get_cookies():
        if cookie.get('name', '') in index_cookie:
            index_cookie.update({
                cookie.get('name'): cookie.get('value')
            })
    for cookie in driver.get_cookies():
        print(f"cookie name -> {cookie.get('name')} cookies value -> {cookie.get('value')}")
    return export_key[0], index_cookie
