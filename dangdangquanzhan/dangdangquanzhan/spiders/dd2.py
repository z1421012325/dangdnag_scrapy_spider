# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re,json
from lxml import etree

from scrapy_redis.spiders import RedisCrawlSpider


# class Dd2Spider(CrawlSpider):
#     name = 'dd2'
#     allowed_domains = ['dangdang.com']
#     start_urls = ['http://category.dangdang.com/?ref=www-0-C']
#
class Dd2Spider(RedisCrawlSpider):
    name = 'dd2'
    allowed_domains = ['dangdang.com']
    # start_urls = ['http://category.dangdang.com/?ref=www-0-C']

    redis_key = 'start_url'

    cp = ['图书','音像/杂志']

    fuwu_url = 'http://product.dangdang.com/index.php?r=' \
               'callback%2Fscore-service&productId={cid}' \
               '&shopId={sid}&isGiftPackaging=0&isSupportReturnPolicy=1&categoryPath={cat_id}&isPod=0'

    pl_url = 'http://product.dangdang.com/index.php?r=comment%2Flist' \
             '&productId={cid}&categoryPath={cat_id}&mainProductId={cid1}&mediumId={mid}&pageIndex={pages}'

    tsjg_url = 'http://product.dangdang.com/index.php?r=callback%2Fspu-prod&productId={cid}&shopId=0'

    rules = (
        # Rule(LinkExtractor(allow=r'http://category.dangdang.com/c.*?.html',restrict_xpaths='//div[@class="classify_con"]'),follow=True),                   # 总分类
        Rule(LinkExtractor(allow=r'http://category.dangdang.com/c.*?.html',
                           restrict_xpaths='//div[@class="classify_con"]'),),

        # Rule(LinkExtractor(allow=r'http://category.dangdang.com/c.*?.html',restrict_xpaths='//ul[@class="filtrate_list"]/li'), follow=True),               # 细分类
        Rule(LinkExtractor(allow=r'http://category.dangdang.com/c.*?.html',
                           restrict_xpaths='//ul[@class="filtrate_list"]/li'),),

        Rule(LinkExtractor(allow=r'http://category.dangdang.com/pg.*?.html'),follow=True),                 # 翻页

        Rule(LinkExtractor(allow=r'http://category.dangdang.com/\d+.html'),callback='parse_xq', follow=True),    # 详情页

    )


    def parse_xq(self, response):
        item = {}

        item['classification'] = response.xpath('//div[@class="breadcrumb"]/a[1]/b/text()').get()
        for i in self.cp:
            if i in item['classification']:
                item['classification1'] = response.xpath('//div[@class="breadcrumb"]/a[2]/text()').get()
                item['classification2'] = response.xpath('//div[@class="breadcrumb"]/a[3]/text()').get()
                item['title'] = response.xpath('//div[@class="name_info"]//h1/@title').get()
                item['url'] = response.url
                item['jj'] = response.xpath('//h2/span[1]/@title').get()

                try:
                    item['shop'] = response.xpath('//span[@class="dang_red"]/text()').get().strip()
                except:
                    item['shop'] = response.xpath('//span[@class="title_name"]/span/a/@title').get()

                item['images'] = set(response.xpath('//ul[@id="mask-small-list-slider"]/li/a/@data-imghref').getall())
                item['pl_count'] = response.xpath('//a[contains(@dd_name,"评论数")]/text()').get()
                item['dzs_price'] = response.xpath('//a[contains(@dd_name,"电子书价")]/text()').get()

                item['authos'] = response.xpath('//a[contains(@dd_name,"作者")]//text()').getall()
                item['cbs'] = response.xpath('//a[contains(@dd_name,"出版社")]//text()').get()

                try:
                    cbsj = ''.join(map(lambda x:x.strip(),response.xpath('//div[@class="messbox_info"]//span/text()').getall()))
                    cbsj = cbsj.split('出版时间:')[1].split('月')[0]
                    item['cbsj'] = cbsj+'月'
                except:
                    item['cbsj'] = None

                item['pro_content'] = ' '.join(response.xpath('//div[@class="pro_content"]/ul/li//text()').getall())



                cid = re.findall('(\d+)',response.url)[0]
                sid = re.findall('"shopId":"(\d+)"', response.text)[0]
                cat_id = re.findall('"categoryPath":"(.*?)"', response.text)[0]
                mid = re.findall('"mediumId":"(\d+)"', response.text)[0]
                pages = round(int(item['pl_count']) / 10)

                price_url = self.tsjg_url.format(cid=cid)
                fw_url = self.fuwu_url.format(cid=cid,sid=sid,cat_id=cat_id)
                pl_urls = self.pl_url.format([self.pl_url.format(cid=cid,cat_id=cat_id,cid1=cid,mid=mid,pages=page)for page in range(1,pages+1)])

                yield scrapy.Request(url=price_url,
                                     callback=self.parse_jg,
                                     meta={'item':(item,fw_url,pl_urls)})



            # 常规物品
            else:
                item['classification1'] = response.xpath('//div[@class="breadcrumb"]/a[2]/text()').get()
                item['classification2'] = response.xpath('//div[@class="breadcrumb"]/a[3]/text()').get()
                item['title'] = response.xpath('//div[@class="name_info"]//h1/@title').get()
                item['shop'] = response.xpath('//span[@class="title_name"]/span/a/text()').get()
                item['url'] = response.url
                item['images'] = set(response.xpath('//ul[@id="mask-small-list-slider"]/li/a/@data-imghref').getall())
                item['pl_count'] = response.xpath('//div[@class="pinglun"]//a/text()').get()
                item['price'] = ''.join(map(lambda x:x.strip(),response.xpath('//p[@id="dd-price"]//text()').getall()))
                item['pro_content'] = ' '.join(response.xpath('//div[@class="pro_content"]/ul/li//text()').getall())


                # fw 和 pl
                cid = re.findall('(\d+)',response.url)[0]
                sid = re.findall('"shopId":"(\d+)"',response.text)[0]
                cat_id = re.findall('"categoryPath":"(.*?)"',response.text)[0]
                fw_url = self.fuwu_url.format(cid=cid,sid=sid,cat_id=cat_id)

                mid = re.findall('"mediumId":"(\d+)"',response.text)[0]
                pages = round(int(item['pl_count'])/10)
                pl_urls = [self.pl_url.format(cid=cid,cat_id=cat_id,cid1=cid,mid=mid,pages=page)for page in range(1,pages+1)]


                yield scrapy.Request(url=fw_url,callback=self.parse_fw,meta={'item':(item,pl_urls)})

    def parse_fw(self, response):
        item,pl_urls = response.meta.get('item')

        res = json.loads(response.text)['data']['data']['data']
        html = etree.HTML(res)
        item['fl'] = html.xpath('//a/text()')

        # pl = []
        # for index,pl_url in enumerate(pl_urls):
        #     print('这是第 {} 个pl'.format(index))
        #     pl.append(scrapy.Request(url=pl_url,callback=self.parse_pl))
        #
        # item['pl'] = pl

        print(item)
        # yield item


    def parse_pl(self,response):
        res = json.loads(response.text)['data']['data']['data']
        html = etree.HTML(res)
        pl_content = html.xpath('//div[@ class="describe_detail"]/span/text()')
        return pl_content


    def parse_jg(self,response):
        item,fw_url,pl_urls = response.meta.get('item')

        item['price'] = json.loads(response.text)['data']['minPrice']

        yield scrapy.Request(url=fw_url, callback=self.parse_fw, meta={'item': (item, pl_urls)})
