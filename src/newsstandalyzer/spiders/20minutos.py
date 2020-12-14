"""
Daily web scraping from different sections of 20minutos newspaper
"""
from abc import ABC
from datetime import datetime
import logging
import yaml
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from newsstandalyzer.db.db import NewsDB

log = logging.getLogger(__name__)


class Spider20minutos(CrawlSpider, ABC):
    name = "20minutos"
    start_urls = ['https://www.20minutos.es/']
    allowed_domains = ['20minutos.es']
    download_delay = 1
    custom_settings = {
      'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Ubuntu Chromium/71.0.3578.80 Chrome/71.0.3578.80 Safari/537.36'
    }
    rules = (
        Rule(LinkExtractor(restrict_xpaths=['//div[@class="sections-col"]/ul/li'],
                           deny_domains=['blogs.20minutos.es'],
                           deny=['/archivo', '/gonzoo', '/gastronomia', '/opinion', '/fotos', '/videos'])),
        Rule(LinkExtractor(allow=r'/noticia',
                           restrict_xpaths=['//article[contains(@class, "media")]'],
                           deny_domains=['blogs.20minutos.es'],
                           deny=['/archivo', '/opinion', '/fotos', '/videos']),
             callback="parse_article"),
        Rule(LinkExtractor(allow=r'/(\d+)',
                           deny_domains=['blogs.20minutos.es'],
                           deny=['/archivo', '/opinion', '/fotos', '/videos'])),
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
            return datetime.strptime(datetime_str.split("-")[0].strip(), "%d.%m.%Y")
        else:
            log.warning(msg="Unknown type for datetime. Returning None.")
            return None

    def parse_article(self, response):
        url = response.url
        category_1 = response.xpath('//ul[contains(@class, "section-menu-small")]//h1//text()').get()
        category_2 = response.xpath('//ul[contains(@class, "default-menu")]//li[1]//a//text()').get()
        category = category_1 if not None else category_2
        title = response.xpath('//h1[@class="article-title "][@id="m25-24-26"]/text()').get()
        subtitle = []
        for node in response.xpath(
                '//section[@class="article-titles"]/div[@class="article-intro "][@id="m30-29-31"]//ul//li'):
            subtitle.append(node.xpath('string()').get())
        subtitle = " ".join(subtitle)
        body = []
        for node in response.xpath('//div[contains(@class, "article-text")]/p'):
            body.append(node.xpath('string()').get())
        body = " ".join(body)
        summary = ""
        tags = ""
        date = response.xpath('//section[@class="article-titles"]//span[@class="article-date"]/a/text()').get()
        date = self.datetime_format(date)
        author = response.xpath('//section[@class="article-titles"]/span[@class="article-author"]//strong/text()').get()
        references = ""
        newspaper = "20minutos"
        country = "ES"

        # Store scraped data into db
        document = {
            "title": title,
            "subtitle": subtitle,
            "category": category,
            "tags": tags,
            "date": date,
            "author": author,
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
    process.crawl(Spider20minutos)
    process.start()
