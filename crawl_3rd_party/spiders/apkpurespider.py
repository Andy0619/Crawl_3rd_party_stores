# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from crawl_3rd_party.items import Crawl3RdPartyItem
from lxml import etree
import requests

class ApkpurespiderSpider(CrawlSpider):
    name = 'apkpurespider'
    allowed_domains = ['apkpure.com','winudf.com']
    start_urls = ['https://apkpure.com/medical?page=1']
    # start_urls = []
    # https://apkpure.com/health_and_fitness
    # https://apkpure.com/medical
    # for i in range(1,24):
    #     start_urls.append('https://apkpure.com/medical?page='+str(i))

    rules = (
        Rule(LinkExtractor(allow=('https://apkpure.com/medical\?page=',)), follow=True, callback='parse_link'),
    )

    def parse_link(self,response):
        print(response.url)
        urls = response.xpath('//ul[@id="pagedata"]/li/div[1]/a[1]/@href').extract()
        for url in urls:
            yield scrapy.Request(url='https://apkpure.com' + url, callback=self.parse_item)


    def parse_item(self,response):
        # for title in response.xpath('/html'):
        item = Crawl3RdPartyItem()
        item["ID"] = "Apkpure_"+response.request.url.split('/')[-1]
        item["Name"] = response.xpath('//div[@class="title-like"]/h1/text()').extract_first()
        item["Developer"] = response.xpath('/html/body/div[6]/div[1]/div[2]/div[1]/div/p[1]/text()').extract_first()
        address = response.request.url
        yield scrapy.Request(url=address+"/versions", meta={'key': item}, callback=self.parse_versions)

    def parse_versions(self,response):
        # print('start parse versions')
        item = response.meta['key']
        versions = response.xpath('/html/body/div[3]/div[1]/div[3]/ul/li')
        # print(versions)
        item["Version"]=[]
        item["Updated"]=[]
        item["headers"] = b";".join(response.headers.getlist("Set-Cookie")).decode('utf-8')
        item["file_urls"]=[]
        if len(versions) >= 1:
            for i in range(len(versions)):
                version_url = "https://apkpure.com"+versions[i].xpath('a[1]/@href').extract_first()
                version_genre = versions[i].xpath('a[1]/div[@class="ver-item"]/div[@class="ver-item-wrap"]/span[contains(@class,"ver-item-t")]/text()').extract()
                # print(version_url)
                # print(version_genre)
                can_use = 1
                for genre in version_genre:
                    # these versions need to download xapk format file, which we can't analyse
                    if (genre == "APKs") or (genre == "XAPK") or (genre == "OBB") or len(versions[i].xpath('a[1]/div[@class="ver-item"]/div')) >=3:
                        can_use = 0
                if(can_use):
                    r = requests.get(version_url)
                    selector = etree.HTML(r.text)
                    directlink = selector.xpath('//a[@id="download_link"]/@href')[0]
                    item["Version"].append(versions[i].xpath(
                        'a[1]/div[@class="ver-item"]/div[@class="ver-item-wrap"]/span[@class="ver-item-n"]/text()').extract_first())
                    item["Updated"].append(versions[i].xpath(
                        '//p[@class="update-on"]/text()').extract_first())
                    item["file_urls"].append(directlink)
            return item
