import requests
import arrow

params = (
    ('query', '\u533A\u5757\u94FE'),
    ('start_time', arrow.utcnow().timestamp - (3600 * 24 * 7)),
    ('end_time', arrow.utcnow().timestamp),
    ('_', arrow.utcnow().timestamp),
)


def get_headers(cookies):
    return {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f"https://search.weixin.qq.com/cgi-bin/h5/wxindex/detail.html?q=%e5%8c%ba%e5%9d%97%e9%93%be&pass_ticket={cookies.get('pass_ticket')}",
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }


def get_index_data(cookies):
    response = requests.get('https://search.weixin.qq.com/cgi-bin/searchweb/getwxindex', headers=get_headers(cookies),
                            params=params, cookies=cookies)
    if response.status_code != 200:
        return None
    return response.json()
