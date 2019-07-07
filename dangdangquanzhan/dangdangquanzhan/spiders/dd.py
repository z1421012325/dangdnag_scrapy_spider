# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re


class DdSpider(CrawlSpider):
    name = 'dd'
    allowed_domains = ['dangdang.com']
    start_urls = ['http://category.dangdang.com/?ref=www-0-C']

    pl_url = 'http://product.dangdang.com/index.php?r=comment%2Flist&productId={}&categoryPath={}&mainProductId={}&mediumId=0&pageIndex={}'
    pj_url = 'http://product.dangdang.com/index.php?r=comment%2Flabel&productId={}&categoryPath={}'

    rules = (
        Rule(LinkExtractor(allow=r'http://category.dangdang.com/c.*?'), callback='parse_item'),)


    def parse_item(self, response):
        # 如果初始页面total数量超过页数统计,则细分分类
        total = int(response.xpath('//span[@class="sp total"]/em/text()').get())

        if total >= 100*48 and re.findall('dangdang.com/cid\d+.html',response.url):
            hrefs = response.xpath('//ul[@class="filtrate_list"]/li//a/@href').getall()
            for href in hrefs:
                if 'javascri' in href:
                    continue
                href = response.urljoin(href)
                scrapy.Request(url=href,callback=self.parse_item)
        # cp页面
        elif total >= 100*60 and re.findall('dangdang.com/cp\d+.\d+.\d+.\d+.\d+.\d+.html',response.url):
            hrefs = response.xpath('//ul[@class="filtrate_list"]/li//a/@href').getall()
            for href in hrefs:
                if 'javascri' in href:
                    continue
                href = response.urljoin(href)
                scrapy.Request(url=href, callback=self.parse_item)
        # 为0不抓取
        elif total == 0:pass


        else:
            if 'dangdang.com/cid' in response.url:
                item = {}

                # 常规物品列表页
                classification1 = response.xpath('//div[@class="crumbs_fb_left"]/a[2]/text()').get()
                classification2 = response.xpath('//div[@class="crumbs_fb_left"]/div[1]/a[1]/text()').get()
                classification3 = response.xpath('//div[@class="crumbs_fb_left"]/div[2]/a[1]/text()').get()

                lis = response.xpath('//div[@id="search_nature_rg"]/ul/li')
                for li in lis:
                    href = li.xpath('./a/@href').get()
                    # cp封面是js加载的,需要滑动,但是这是个实验班的,我就不弄了,如果正式版请到详情页抓取
                    img = response.urljoin(li.xpath('./a/img/@src').get())
                    comment = li.xpath('.//p[@class="star"]/a/text()').get()
                    title = li.xpath('.//p[@class="name"]/a/text()').get()
                    price = li.xpath('.//p[@class="price"]/span/text()').get()

                    item['classification1'] = classification1
                    item['classification2'] = classification2
                    item['classification3'] = classification3
                    item['title'] = title
                    item['href'] = href
                    item['img'] = img
                    item['price'] = price.replace('¥', '')
                    item['comment'] = comment

                    # 单纯抓取信息,之后再通过其他方法抓取评论 cat_path 需要在详情页源码中找
                    # _cat_path = response.xpath('//div[@class="crumbs_fb_left"]/div[2]/a[1]/@href').get()
                    # item['pl']['cat_path'] = re.findall('(\d+.\d+.\d+.\d+.\d+.\d+)',_cat_path)[0]
                    # item['pl']['cid'] = re.findall('(\d+)',response.url)
                    # item['pl']['pages'] = int(item['comment'])/10+1

                    yield item

                next_url = response.urljoin(response.xpath('//li[@class="next"]/a/@href').get())
                if next_url:
                    yield scrapy.Request(url=next_url,callback=self.parse_item)


                # -------------------------------------------------------------------------------------------
                # TODO 深入详情页  比如抓取评论
                # lis = response.xpath('//div[@id="search_nature_rg"]/ul/li')
                # item = {}
                # for li in lis:
                #     item['href'] = response.urljoin(li.xpath('./a/@href').get())
                #     item['img'] = li.xpath('./a/img/@src').get()
                #     item['comment'] = li.xpath('.//p[@class="star"]/a/text()').get()
                #     item['title'] = li.xpath('.//p[@class="name"]/a/text()').get()
                #     item['price'] = li.xpath('.//p[@class="price"]/span/text()').get()
                #
                #     # _cat_path = response.xpath('//div[@class="crumbs_fb_left"]/div[2]/a[1]/@href').get()
                #     # cat_path = re.findall('(\d+.\d+.\d+.\d+.\d+.\d+)',_cat_path)[0]
                #
                #     # scrapy.Request(url=item['href'],callback=self.parse_content,meta={'meta':item})
                #     yield item
                #
                # next_url = response.urljoin(response.xpath('//li[@class="next"]/a/@href').get())
                # if next_url:
                #     yield scrapy.Request(url=next_url, callback=self.parse_item)



            elif 'dangdang.com/cp' in response.url:
                item = {}

                # 需要抓取图书页面的作者名字,
                # 如果深入则根据情况注释掉分类,在详情页抓取
                classification1 = response.xpath('//div[@class="select_frame"][1]/a/text()').get()
                classification2 = response.xpath('//div[@class="select_frame"][2]/a/text()').get()
                classification3 = response.xpath('//div[@class="select_frame"][3]/a/text()').get()

                lis = response.xpath('//ul[@class="bigimg"]/li')
                for li in lis:
                    href = li.xpath('./a/@href').get()
                    img = response.urljoin(li.xpath('./a/img/@src').get())
                    comment = li.xpath('.//p[@class="search_star_line"]/a/text()').get()
                    title = li.xpath('./a/@title').get()
                    price = li.xpath('.//p[@class="price"]/span[1]/text()').get()

                    autho = li.xpath('.//p[@class="search_book_author"]/span[1]/a[1]/text()').get()
                    if not autho:
                        autho =None

                    datetime = li.xpath('.//p[@class="search_book_author"]/span[2]//text()').get()
                    if not datetime:
                        datetime = None

                    press = li.xpath('.//p[@class="search_book_author"]/span[3]/a/@title').get()
                    if not press:
                        press = None

                    introduction = li.xpath('.//p[@class="detail"]/text()').get()
                    if not introduction:
                        introduction = None

                    item['classification1'] = classification1
                    item['classification2'] = classification2
                    item['classification3'] = classification3
                    item['title'] = title
                    item['autho'] = autho
                    item['href'] = href
                    item['img'] = img
                    item['price'] = price.replace('¥','')
                    item['comment'] = comment
                    item['press'] = press
                    item['introduction'] = introduction
                    item['datetime'] = str(datetime)

                    # _cat_path = response.xpath('//div[@class="crumbs_fb_left"]/div[2]/a[1]/@href').get()
                    # item['cat_path'] = re.findall('(\d+.\d+.\d+.\d+.\d+.\d+)', _cat_path)[0]
                    # item['cid'] = re.findall('(\d+)', response.url)
                    # item['pl_pages'] = int(item['comment']) / 10 + 1

                    yield item

                next_url = response.urljoin(response.xpath('//li[@class="next"]/a/@href').get())
                if next_url:
                    yield scrapy.Request(url=next_url, callback=self.parse_item)























                # -------------------------------------------------------------------------------------------
                # TODO 深入详情页 比如抓取评论
                # lis = response.xpath('//div[@id="search_nature_rg"]/ul/li')
                # item = {}
                # for li in lis:
                #     item['href'] = response.urljoin(li.xpath('./a/@href').get())
                #     item['img'] = li.xpath('./a/img/@src').get()
                #     item['comment'] = li.xpath('.//p[@class="search_star_line"]/a/text()').get()
                #     item['title'] = li.xpath('./a/@title').get()
                #     item['price'] = li.xpath('.//p[@class="price"]/span[1]/text()').get()
                #
                #     item['autho'] = li.xpath('.//p[@class="search_book_author"]/span[1]/a[1]/text()').get()
                #     if not item['autho']:
                #         item['autho'] = None
                #
                #     item['datetime'] = li.xpath('.//p[@class="search_book_author"]/span[2]//text()').get()
                #     if not item['datetime']:
                #         item['datetime'] = None
                #
                #     item['press'] = li.xpath('.//p[@class="search_book_author"]/span[3]/a/@title').get()
                #     if not item['press']:
                #         item['press'] = None
                #
                #     item['introduction'] = li.xpath('.//p[@class="detail"]/text()').get()
                #     if not item['introduction']:
                #         item['introduction'] = None
                #

                #     # 这个提取也有问题,cat_path 提取方法不同 ,需要进入详情页源码抓取
                #     # cid = re.findall('(\d+)',item['href'])[0]
                #     # _cat_path = response.xpath('//div[@class="crumbs_fb_left"]/div[2]/a[1]/@href').get()
                #     # cat_path = re.findall('(\d+.\d+.\d+.\d+.\d+.\d+)', _cat_path)[0]
                #     # pages = int(item['comment'])/10
                #     # todo 这里有点问题,pl会出现重复,除非在保存时进行updata更新
                #     # pl_urls = [self.pl_url.format(cid,cat_path,cid,page)for page in range(1,int(pages)+1)]
                #     # for pl_url in pl_urls:
                #     #     scrapy.Request(url=pl_url,callback=self.parse_content,meta={'meta':item})
                #     # scrapy.Request(url=item['href'], callback=self.parse_content, meta={'meta': item})
                #

                # next_url = response.urljoin(response.xpath('//li[@class="next"]/a/@href').get())
                # if next_url:
                #     yield scrapy.Request(url=next_url, callback=self.parse_item)



    def parse_content(self,response):
        item = response.meta.get('meta')

        # todo 根据情况来,比如抓取评论
