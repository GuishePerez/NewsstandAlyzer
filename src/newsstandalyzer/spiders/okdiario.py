"""
Daily web scraping from different sections of OkDiario newspaper
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


class SpiderOkDiario(CrawlSpider, ABC):
    name = "okdiario"
    start_urls = ['https://okdiario.com/']
    allowed_domains = ['okdiario.com']
    download_delay = 1
    custom_settings = {
      'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Ubuntu Chromium/71.0.3578.80 Chrome/71.0.3578.80 Safari/537.36'
    }
    rules = (
        Rule(LinkExtractor(restrict_xpaths=['//ul[@class="okdiario-secciones-menu-navegacion-ul"]//li'],
                           deny_domains=['okjuridico.okdiario.com'],
                           deny=['/opinion', '/fotos', '/videos', '/look', '/trailer', '/diariomadridista',
                                 '/podcast', '/ok-vs-ko', '/loteria', '/recetas', '/howto']),
             ),
        Rule(LinkExtractor(restrict_xpaths=['//article[contains(@class, "article fillContain")]'],
                           deny=['/opinion', '/fotos', '/videos', '/look', '/trailer', '/diariomadridista',
                                 '/podcast', '/ok-vs-ko', '/loteria', '/recetas', '/howto']),
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
            return datetime.strptime(datetime_str.split(" ")[0].strip(), "%d/%m/%Y")
        else:
            log.warning(msg="Unknown type for datetime. Returning None.")
            return None

    def parse_article(self, response):
        url = response.url
        category = url.split("/")[3]
        title = response.xpath('//h1[@class="entry-title"]//text()').get()
        subtitle = response.xpath('//header[@class="entry-header"]/span[@class="pre-title"]/text()').get()
        body = []
        for node in response.xpath('//div[contains(@class, "entry-content")][@id="contentid-0"]/p'):
            body.append(node.xpath('string()').get())
        body = " ".join(body)
        summary = ""
        tags = []
        for node in response.xpath('//div[@class="topics"]/ul/li'):
            tag = node.xpath('string()').get()
            if tag.strip() == 'Temas:' or tag in tags:
                continue
            else:
                tags.append(tag)
        date = response.xpath('//time[@class="date"]/text()').get()
        date = self.datetime_format(date)
        author = response.xpath('//li[@class="author-name"]/strong/a/text()').get()
        references = ""
        newspaper = "Ok Diario"
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
    process.crawl(SpiderOkDiario)
    process.start()
