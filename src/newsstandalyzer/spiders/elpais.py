"""
Daily web scraping from different sections of ElPais newspaper
"""
from abc import ABC

from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class SpiderElPais(CrawlSpider, ABC):
    name = "elpais"
    allowed_domains = ['elpais.com']
    download_delay = 1
    custom_settings = {
      'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Ubuntu Chromium/71.0.3578.80 Chrome/71.0.3578.80 Safari/537.36'
    }
    rules = (
        Rule(LinkExtractor(allow=r'/(\d{4})-(\d{2})-(\d{2})',
                           deny=r'/hemeroteca',
                           restrict_xpaths=['//div[contains(@class, "section")]']),
             follow=False,
             callback="parse_article"),
    )

    def __init__(self, args):
        super().__init__()
        self.start_urls = args[0]

    def parse_article(self, response):
        url = response.url
        print(url)
        # category = response.referer
        title = response.xpath('//div[@id="article_header"]/h1/text()').get()
        print(title)
        subtitle = response.xpath('//div[@id="article_header"]/h2/text()').get()
        print(subtitle)
        body = response.xpath('//div[contains(@class, "article_body")]/p/text()').get()
        print(body)
        summary = ""
        tags = response.xpath('//ul[contains(@class, "tags_list")]/li/a/text()').get()
        print(tags)
        date = response.xpath('//div[contains(@class, "a_pt")]/a/text()').get()
        print(date)
        author = response.xpath().get()
        # references = response.xpath().get()
        # newspaper = "El Pais"
        # country = "ES"


if __name__ == '__main__':
    start_urls = ["https://elpais.com/internacional",
                  "https://elpais.com/espana",
                  "https://elpais.com/economia",
                  "https://elpais.com/sociedad",
                  "https://elpais.com/clima-y-medio-ambiente",
                  "https://elpais.com/ciencia",
                  "https://elpais.com/tecnologia",
                  "https://elpais.com/cultura",
                  "https://elpais.com/deportes",
                  "https://elpais.com/television",
                  "https://elpais.com/gente"]
    process = CrawlerProcess()
    for url in start_urls:
        process.crawl(SpiderElPais, [[url]])
        process.start()
