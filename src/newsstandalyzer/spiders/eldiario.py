"""
Daily web scraping from different sections of ElDiario newspaper
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

MONTHS_MAPPER = {
    "enero": "1",
    "febrero": "2",
    "marzo": "3",
    "abril": "4",
    "mayo": "5",
    "junio": "6",
    "julio": "7",
    "agosto": "8",
    "septiembre": "9",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12"
}


class SpiderElDiario(CrawlSpider, ABC):
    name = "eldiario"
    start_urls = ['https://www.eldiario.es/']
    allowed_domains = ['eldiario.es']
    download_delay = 1
    custom_settings = {
      'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Ubuntu Chromium/71.0.3578.80 Chrome/71.0.3578.80 Safari/537.36'
    }
    rules = (
        Rule(LinkExtractor(restrict_xpaths=['//div[@class="cmp-main-menu-tablet"]/div/ul//li'],
                           deny_domains=['vertele.eldiario.es'],
                           deny=['/redaccion', '/opinion', '/fotos', '/videos', '/opinionsocios', '/blog', '/blogs',
                                 '/contracorriente', '/carnecruda', '/arsenioescolar', '/ultima-llamada', '/retrones',
                                 '/comoyporque', '/tumejoryo', '/cienciacritica', '/caballodenietzsche', '/contrapoder',
                                 '/interferencias', '/micromachismos', '/campobase', '/piedrasdepapel',
                                 '/murcia-y-aparte', '/emprende-a-diario', '/palabras-clave', '/edcreativo',
                                 '/de-ciencia']),
             ),
        Rule(LinkExtractor(restrict_xpaths=['//h2[contains(@class, "ni-title")]'],
                           deny=['/redaccion', '/opinion', '/fotos', '/videos', '/opinionsocios', '/blog', '/blogs',
                                 '/contracorriente', '/carnecruda', '/arsenioescolar', '/ultima-llamada', '/retrones',
                                 '/comoyporque', '/tumejoryo', '/cienciacritica', '/caballodenietzsche', '/contrapoder',
                                 '/interferencias', '/micromachismos', '/campobase', '/piedrasdepapel',
                                 '/murcia-y-aparte', '/emprende-a-diario', '/palabras-clave', '/edcreativo',
                                 '/de-ciencia']),
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
            dt = datetime_str.split("de")
            dt = [str(s).strip() if i != 1 else MONTHS_MAPPER[str(s).strip()] for i, s in enumerate(dt)]
            return datetime.strptime(".".join(dt), "%d.%m.%Y")
        else:
            log.warning(msg="Unknown type for datetime. Returning None.")
            return None

    def parse_article(self, response):
        url = response.url
        category = url.split("/")[3]
        title = response.xpath('//h1[@class="title"]//text()').get()
        subtitle = response.xpath('//div[@class="news-header"]/ul[@class="footer"]/li//text()').get()
        body = []
        for node in response.xpath('//div[contains(@class, "partner-wrapper article-page__body-row")]/div/p'):
            body.append(node.xpath('string()').get())
        body = " ".join(body)
        summary = ""
        tags = []
        for node in response.xpath('//ul[@class="tags-wrapper"]/li'):
            tag = node.xpath('string()').get()
            if tag == '\xa0\xa0/\xa0\xa0' or tag in tags:
                continue
            else:
                tags.append(tag)
        date = response.xpath('//div[@class="date-comments-wrapper"]/time/span/text()').get()
        date = self.datetime_format(date)
        author = response.xpath('//div[@class="info-wrapper"]/p/a/text()').get() if not None \
            else response.xpath('//div[@class="info-wrapper"]/p/text()').get()
        references = ""
        newspaper = "El Diario"
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
    process.crawl(SpiderElDiario)
    process.start()
