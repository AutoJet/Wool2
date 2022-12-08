# -*- coding: utf-8 -*-
"""
    new Env("雅迪 微信小程序")
    Author: AutoJet
    cron: 一天一次
    变量格式: export yadick="Bearer xxxxxxx"    多账号用 换行 分割

    21.12.7    v1.0.0
"""

import json
import os
import random
import time

import requests


def get_yiyan(min_len=25, max_len=200):
    url = 'https://v1.hitokoto.cn'
    params = {
        'encode': 'json',
        'min_length': min_len,
        'max_length': max_len,
    }
    try:
        res = requests.get(url, params=params)
        res_json = res.json()
        content = res_json['hitokoto']  # + ' --' + (res_json['from'] if res_json['from'] else '佚名')
    except Exception as e:
        print(e)
        content = ''
    return content


def download_image_from_url(url):
    try:
        header = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 UBrowser/6.1.2107.204 Safari/537.36'
        }
        res = requests.get(url, headers=header)
        if res.status_code == 200:
            return res.content
    except Exception as e:
        print(e)
    return None


def get_image():
    api_list = [
        'https://api.r10086.com/img-api.php?type=风景系列{}'.format(random.randint(1, 10)),
        'https://api.likepoems.com/img/sina/nature',
    ]
    random.shuffle(api_list)
    for api in api_list:
        image_bytes = download_image_from_url(api)
        if image_bytes is not None:
            return image_bytes
    return None


class Yadea:
    def __init__(self, token):
        self.token = token
        self.phone = None
        self.nick_name = None
        self.points = None
        self.mobile = None
        self.user_id = None

    def sign(self):
        path = "app-api/ygSign/in"
        data = {
            "headImage": "http://avatar.cwens.com/avatar_272.png",
            "nickName": self.nick_name,
            "signDate": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "userId": self.user_id
        }
        res_json = self.http(method='post', path=path, data=data)
        return '签到成功' if res_json else '签到失败'

    def share(self, content_id):
        path = "app-api/integral/user/share/{}/{}".format(self.user_id, content_id)
        res_json = self.http(method='post', path=path, data='')
        return bool(res_json)

    def comment(self, authotId, fromId):
        path = "app-api/comment/toComment"
        data = {
            "authotId": authotId,
            "content": "👍",
            "fromId": fromId,
            "type": 0
        }
        res_json = self.http(method='post', path=path, data=data)
        return bool(res_json)

    def upload_img(self):
        image_bytes = [get_image() for _ in range(3)]
        image_urls = []
        for image_byte in image_bytes:
            if image_byte is None:
                continue
            timestamp = '{:.6f}'.format(time.time() * 1000)
            files = {'file': (timestamp + '.jpeg', image_byte, "image/jpeg")}
            path = 'common-api/byton/oss/upload'
            res_data = self.http(method='file', path=path, files=files)
            if res_data is None:
                continue
            image_urls.append(res_data['object'])
        random.shuffle(image_urls)
        return image_urls

    def publish(self):
        img_urls = self.upload_img()
        content = get_yiyan()
        data = {
            "id": "", "address": "", "lat": "", "lon": "",
            "postContent": content,
            "imageList": [{"wide": None, "high": None, "annexUrl": url} for url in img_urls],
            "activityType": 2
        }
        path = 'app-api/post/app/add'
        res_data = self.http(method='post', path=path, data=data)
        return '发表成功：' + content if res_data else '发表失败'

    def triple(self):
        path = 'app-api/content/app/recommend?pageNum=1&pageSize=10&viewType=2'
        res_data = self.http(method='get', path=path)
        contents = res_data['object']['records']
        random.shuffle(contents)
        share_num, comment_num = 0, 0
        for content in contents[:2]:
            id = content['id']
            authorId = content['authorId']
            share_num += self.share(id)
            comment_num += self.comment(authorId, id)
            time.sleep(16.8)
        return '分享*{} 评论*{}'.format(share_num, comment_num)

    def claim_points_by_id(self, point_id):
        path = "app-api/integral/user/{}/{}".format(self.user_id, point_id)
        res_json = self.http(method='post', path=path, data='')
        return bool(res_json)

    def claim_all_points(self):
        path = 'app-api/integral/user/details'
        params = {"userId": self.user_id}
        res_data = self.http(method='get', path=path, params=params)
        task_list = res_data['object']['details']
        for task in task_list:
            point_id = task['id']
            self.claim_points_by_id(point_id)
        return ''

    def get_user_id(self):
        path = 'app-api/vehicle/owner'
        res_data = self.http(method='get', path=path)
        if res_data:
            self.user_id = res_data['object']['id']
            return True
        return False

    def get_me(self):
        if not self.get_user_id():
            return None
        path = 'app-api/integral/user/details'
        params = {"userId": self.user_id}
        res_data = self.http(method='get', path=path, params=params)
        if res_data is None:
            return None
        # 首次查询
        if self.points is None:
            self.points = res_data['object']['integralValue']
            self.nick_name = res_data['object']['head']['nickName'] if res_data['object']['head'] else ''
            self.phone = res_data['object']['head']['phone'] if res_data['object']['head'] else ''
            return '账户:{} 积分：{}'.format(self.phone, self.points)
        # 再次查询
        else:
            old_points, self.points = self.points, res_data['object']['integralValue']
            return '获得:{} 积分：{}'.format(self.points - old_points, self.points)

    def http(self, method='get', path='', params=None, data=None, files=None):
        if params is None:
            params = {}
        if data is None:
            data = {}
        data = json.dumps(data) if isinstance(data, dict) else data

        URL = 'https://cms-api.op.yadea.com.cn/' + path
        res_json = None
        headers = {
            "Host": "cms-api.op.yadea.com.cn",
            "Connection": "keep-alive",
            "Authorization": self.token,
            "Accept-Encoding": "gzip,compress,br,deflate",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.27(0x18001b37) NetType/4G Language/zh_CN",
        }
        try:
            if method == 'post':
                headers.update({
                    "Content-Type": "application/json;charset=utf-8",
                    "Content-Length": str(len(data)),
                })
                res = requests.post(URL, headers=headers, params=params, data=data)
            elif method == 'file':
                res = requests.post(URL, headers=headers, params=params, files=files)
            else:
                res = requests.get(URL, headers=headers, params=params)
            if DEBUG:
                print(path)
                print(res.text)
            res_json = res.json()
            if not res_json["code"] == "200":
                print(path)
                print(res.text)
                res_json = None
            res.close()
        except Exception as e:
            print(e)
        return res_json


if __name__ == '__main__':
    DEBUG = False
    access_tokens = []

    if 'yadick' in os.environ:
        access_tokens.extend(os.environ['yadick'].split('\n'))
    access_tokens = set(access_tokens)

    if not access_tokens:
        print('CK为空！')
        exit(0)

    msg_list = ['雅迪WX']
    avail_qr = None
    for idx, access_token in enumerate(access_tokens):
        qr = Yadea(token=access_token)
        user_detail = qr.get_me()
        if not user_detail:
            msg_list.append('账户{}：账户失效/格式错误'.format(idx + 1))
            msg_list.append(' -' * 10)
            continue
        msg_list.append(user_detail)
        msg_list.extend([qr.sign(), qr.triple(), qr.publish(), qr.claim_all_points(), qr.get_me()])
        msg_list.append(' -' * 10)
        time.sleep(2.33)

    # 推送函数
    msg = '\n'.join(msg_list)
    print(msg)
    # push(msg)
