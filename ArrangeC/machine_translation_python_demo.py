from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import requests

'''
1.机器翻译2.0，请填写在讯飞开放平台-控制台-对应能力页面获取的APPID、APISecret、APIKey。
 2.目前仅支持中文与其他语种的互译，不包含中文的两个语种之间不能直接翻译。
 3.翻译文本不能超过5000个字符，即汉语不超过15000个字节，英文不超过5000个字节。
 4.此接口调用返回时长上有优化、通过个性化术语资源使用可以做到词语个性化翻译、后面会支持更多的翻译语种。
'''
APPId = ""
APISecret = ""
APIKey = ""
# 术语资源唯一标识，请根据控制台定义的RES_ID替换具体值，如不需术语可以不用传递此参数
#RES_ID = "its_en_cn_word"
# 翻译原文本内容
TEXT = "Hi, I wrote the first part about this story on geoexpat, but I can't access it anymore since I'm no longer in HK. I wanted to share it here to reach a greater audience and maybe help someone avoid a similar fate anyway, so I'm sharing the whole story here."


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema
        pass


# calculate sha256 and encode to base64
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


# build websocket auth request url
def assemble_ws_auth_url(requset_url, method="POST", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    # print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    # print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    # print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)


if __name__ == "__main__":

    url = 'https://itrans.xf-yun.com/v1/its'

    body = {
        "header": {
            "app_id": APPId,
            "status": 3,
            #"res_id": RES_ID
        },
        "parameter": {
            "its": {
                "from": "en",
                "to": "cn",
                "result": {}
            }
        },
        "payload": {
            "input_data": {
                "encoding": "utf8",
                "status": 3,
                "text": base64.b64encode(TEXT.encode("utf-8")).decode('utf-8')
            }
        }
    }

    request_url = assemble_ws_auth_url(url, "POST", APIKey, APISecret)

    headers = {'content-type': "application/json", 'host': 'itrans.xf-yun.com', 'app_id': APPId}
    # print(request_url)
    response = requests.post(request_url, data=json.dumps(body), headers=headers)
    print(headers)
    print(response)
    print(response.content)
    tempResult = json.loads(response.content.decode())
    print('text字段Base64解码后=>' + base64.b64decode(tempResult['payload']['result']['text']).decode())
    input("press sth")
    '''
    text字段Base64解码后=>
    {"from":"en","to":"cn","trans_result":
        {"src":"Hi, I wrote the first part about this story on geoexpat, but I can't access it anymore since I'm no longer in HK. I wanted to share it here to reach a greater audience and maybe help someone avoid a similar fate anyway, so I'm sharing the whole story here.",
        "dst":"嗨，我在GeoExpat上写了这个 故事的第一部分，但我不能再访问它了，因为我已经不在香港了。我想在这里分享它，以获得更多的观众，也许能帮助一些人避免类似的命运，所以我在这里分享整个故事。"
        }
    }
    '''