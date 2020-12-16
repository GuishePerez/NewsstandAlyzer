"""
Daily web scraping from different sections of Heraldo de Aragón newspaper
"""
from abc import ABC
from datetime import datetime
import logging
import yaml
from pathlib import Path
import re

from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from newsstandalyzer.db.db import NewsDB

log = logging.getLogger(__name__)

DATE_PATTERN = re.compile(r'\d{4}/\d+/\d+')


class SpiderHeraldo(CrawlSpider, ABC):
    name = "heraldoaragon"
    start_urls = ['https://www.heraldo.es/']
    allowed_domains = ['heraldo.es']
    download_delay = 1
    custom_settings = {
      'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Ubuntu Chromium/71.0.3578.80 Chrome/71.0.3578.80 Safari/537.36'
    }
    rules = (
        Rule(LinkExtractor(restrict_xpaths=['//ul[@class="default-hamburger1-menu"]//li'],
                           deny_domains=['guia.heraldo.es'],
                           deny=['/opinion', '/fotos', '/videos', '/horoscopo', '/multimedia']),
             ),
        Rule(LinkExtractor(restrict_xpaths=['//div[@class="article-details"]/h1[@class="title"]/a'],
                           deny=['/opinion', '/fotos', '/videos', '/horoscopo', '/multimedia']),
             callback="parse_article"),
    )

    def __init__(self):
        super().__init__()
        # Load DB settings
        db_settings_path = Path(__file__).parent / "../db/db_settings.yaml"
        with db_settings_path.open() as f:
            db_settings = yaml.load(f, Loader=yaml.FullLoader)
        self.db = NewsDB(**db_settings['db_settings'])

    @staticmethod
    def datetime_format(datetime_str: str = None):
        if isinstance(datetime_str, str):
            return datetime.strptime(datetime_str, "%Y/%m/%d")
        else:
            log.warning(msg="Unknown type for datetime. Returning None.")
            return None

    def parse_article(self, response):
        url = response.url
        category = url.split("/")[4]
        title = response.xpath('//h1[@class="title "][@id="m48-47-49"]//text()').get()
        subtitle = response.xpath('//p[contains(@class, "epigraph")][@id="m53-52-54"]/text()').get()
        body = []
        for node in response.xpath('//div[contains(@class, "content-modules")]/p'):
            body.append(node.xpath('string()').get())
        body = " ".join(body)
        summary = ""
        tags = []
        for node in response.xpath('//ul[@class="tags-container"]/li'):
            tag = node.xpath('string()').get()
            tags.append(tag.strip())
        date = re.search(DATE_PATTERN, url).group(0)
        date = self.datetime_format(date)
        authors = []
        for node in response.xpath('//ul[@class="list-authors"]/li'):
            author = node.xpath('string()').get()
            authors.append(author.strip())
        if len(authors) == 1:
            authors = authors[0]
        references = ""
        newspaper = "Heraldo Aragon"
        country = "ES"

        # Store scraped data into db
        document = {
            "title": title,
            "subtitle": subtitle,
            "category": category,
            "tags": tags,
            "date": date,
            "author": authors,
            "references": references,
            "newspaper": newspaper,
            "country": country,
            "summary": summary,
            "body": body,
            "url": url
        }
        self.db.col.insert_one(document=document)


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(SpiderHeraldo)
    process.start()
