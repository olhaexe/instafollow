# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient
import scrapy
from scrapy.pipelines.images import ImagesPipeline
import datetime

mongo_client = MongoClient()


class GbparsePipeline(object):

    def process_item(self, item, spider):
        database = mongo_client[spider.name]
        collection = database[f'{type(item).__name__}_{datetime.datetime.today().strftime("%d_%m_%Y")}']
        collection.insert_one(item)
        return item

class PhotoDownloadPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        if item.get('photos'):
            for img in item.get('photos'):
                try:
                    yield scrapy.Request(img)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        if results:
            item['photos'] = [itm[1] for itm in results]
        return item
