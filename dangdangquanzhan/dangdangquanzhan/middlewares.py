# -*- coding: utf-8 -*-


import user_agent
import requests


class UA_midd(object):
    def process_request(self,request,spider):
        request.headers['User-Agent'] = user_agent.generate_user_agent()
        referer = request.url
        if referer:
            request.headers['Referer'] = referer


class Proxy_midd(object):

    def __init__(self):
        self.ip = ''
        self.url = 'http://188.131.212.24:5010/get/'
        self.count = 0

    def process_request(self, request, spider):

        if self.count == 0 or self.count >=20:
            res = requests.get(url=self.url).content.decode()
            if not 'no' in res:
                self.ip = res
            self.count = 1

        if self.ip:
            request.meta['proxy'] = 'http://' + self.ip
            self.count += 1
        else:
            self.count += 5




    def process_exception(self, request, exception, spider):
        if isinstance(request,TimeoutError):
            self.count += 20
            return request


