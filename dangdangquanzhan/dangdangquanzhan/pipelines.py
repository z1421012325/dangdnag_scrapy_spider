# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from scrapy.conf import settings
import pymysql



class Mongodb_Pipeline(object):

    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client[settings.get('MONGODB_NAME')]

    def process_item(self, item, spider):
        if item:
            coll = item['classification1']
            self.db[coll].insert(dict(item))
        return item


    def close_spider(self):
        self.client.close()


