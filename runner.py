from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from teachers.les5.gbparse import settings
from teachers.les5.gbparse.spiders.geekbrains import GeekbrainsSpider
from teachers.les5.gbparse.spiders.avito import AvitoSpider
from teachers.les5.gbparse.spiders.instagram import InstagramSpider

if __name__ == '__main__':
    scr_settings = Settings()
    scr_settings.setmodule(settings)
    process = CrawlerProcess(settings=scr_settings)
    # process.crawl(GeekbrainsSpider)
    #process.crawl(AvitoSpider)
    process.crawl(InstagramSpider)
    process.start()
