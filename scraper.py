import re
import scrapy
from scrapy.crawler import CrawlerProcess
# This is the corrected import statement
from scrapy_playwright.request import PlaywrightRequest

class CrautosItem(scrapy.Item):
    url = scrapy.Field()
    marca = scrapy.Field()
    modelo = scrapy.Field()
    año = scrapy.Field()
    precio_crc = scrapy.Field()
    img = scrapy.Field()
    kilometraje = scrapy.Field()
    cilindrada = scrapy.Field()
    estilo = scrapy.Field()
    transmision = scrapy.Field()
    combustible = scrapy.Field()
    visto = scrapy.Field()
    detalles = scrapy.Field()

MARCAS = [
    "ACURA", "ALFA ROMEO", "AMC", "ARO", "ASIA", "ASTON MARTIN", "AUDI", "AUSTIN",
    "BAW", "BENTLEY", "BLUEBIRD", "BMW", "BRILLIANCE", "BUICK", "BYD", "CADILLAC",
    "CHANA", "CHANGAN", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DACIA",
    "DAEWOO", "DAIHATSU", "DATSUN", "DODGE/RAM", "DODGE", "RAM", "DONFENG(ZNA)",
    "DONFENG", "ZNA", "EAGLE", "FAW", "FERRARI", "FIAT", "FORD", "FOTON",
    "FREIGHTLINER", "GEELY", "GENESIS", "GEO", "GMC", "GONOW", "GREAT WALL",
    "HAFEI", "HAIMA", "HEIBAO", "HIGER", "HINO", "HONDA", "HUMMER", "HYUNDAI",
    "INFINITI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC", "JAGUAR", "JEEP",
    "JINBEI", "JMC", "JONWAY", "KENWORTH", "KIA", "LADA", "LAMBORGHINI", "LANCIA",
    "LAND ROVER", "LEXUS", "LIFAN", "LINCOLN", "LOTUS", "MACK", "MAGIRUZ",
    "MAHINDRA", "MASERATI", "MAZDA", "MERCEDES BENZ", "MERCURY", "MG", "MINI",
    "MITSUBISHI", "NISSAN", "OLDSMOBILE", "OPEL", "PETERBILT", "PEUGEOT",
    "PLYMOUTH", "POLARSUN", "PONTIAC", "PORSCHE", "PROTON", "RAMBLER", "RENAULT",
    "REVA", "ROLLS ROYCE", "ROVER", "SAAB", "SAMSUNG", "SATURN", "SCANIA", "SCION",
    "SEAT", "SKODA", "SMART", "SOUEAST", "SSANG YONG", "SUBARU", "SUZUKI",
    "TIANMA", "TIGER TRUCK", "TOYOTA", "VOLKSWAGEN", "VOLVO", "WESTERN STAR",
    "YUGO", "ZOTYE",
]

class CarsSpider(scrapy.Spider):
    name = "cars"
    allowed_domains = ["crautos.com"]

    def start_requests(self):
        yield PlaywrightRequest(
            url="https://crautos.com/autosusados/searchresults.cfm?p=1",
            callback=self.parse_list,
            meta={"playwright": True}
        )

    def parse_list(self, response):
        car_links = response.css('form .inventory > a::attr(href)').getall()
        for link in car_links:
            yield response.follow(link, callback=self.parse_detail)

        next_page = response.css('a[title="Página Siguiente"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_list)

    def parse_detail(self, response):
        item = CrautosItem()
        item['url'] = response.url
        headers = response.css('h2::text').getall()
        if len(headers) >= 2:
            full_title_parts = [part.strip() for part in headers[0].upper().split('\n') if part.strip()]
            if len(full_title_parts) == 2:
                full_title, year = full_title_parts
                item['año'] = year
                for marca in MARCAS:
                    if full_title.startswith(marca):
                        item['marca'] = marca
                        item['modelo'] = full_title.replace(marca, '', 1).strip()
                        break
            item['precio_crc'] = re.sub(r'\D', '', headers[1])
        item['img'] = response.css('#largepic::attr(src)').get()
        for row in response.css('#geninfo table tr'):
            cells = [cell.strip() for cell in row.css('td *::text').getall() if cell.strip()]
            if len(cells) == 2:
                key, value = cells
                key = key.lower().replace(':', '')
                if key == 'kilometraje' and value != 'ND':
                    item[key] = re.sub(r'\D', '', value)
                elif key == 'cilindrada':
                    item[key] = re.sub(r'\D', '', value)
                elif key in item.fields:
                    item[key] = value
        yield item

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        "FEEDS": {
            "output.json": {"format": "json"},
        },
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "LOG_LEVEL": "INFO",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,
            "slow_mo": 50,
        },
    })
    process.crawl(CarsSpider)
    process.start()