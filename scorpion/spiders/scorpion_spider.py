import scrapy
from datetime import datetime

class ScorpionSpider(scrapy.Spider):
    name = 'scorpion'
    start_urls = ['https://www.scorpion.com.mx']
    def parse(self, response):
        categories = response.xpath('//a[@class="level-top"]/@href').extract()
        for category in categories:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        products = response.xpath('//a[@class="product-item-link"]/@href').extract()
        for product in products:
            yield scrapy.Request(product, callback=self.parse_product)
        next_page = response.xpath('//a[@class="action next"]/@href').extract_first()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_category)

    
    def filter_price(self, price):
        if price:
            return price.replace('$', '').replace(',', '').replace('c/u', '').strip()
        else:
            return ''

    def parse_product(self, response):
        item = response.xpath('//h1/span/text()').extract_first()
        sku = response.xpath('//div[@itemprop="sku"]/text()').extract_first()
        item_characteristics = response.xpath("//div[@itemprop='description']/text()").extract_first()
        image = response.xpath('//meta[@property="og:image"]/@content').extract_first()
        price_boxes = response.xpath("//div[@class='priceBox']")
        breadcrumbs = response.xpath('//li[contains(@class,"item category")]')
        breadcrumbs_dict = {i: breadcrumbs[i].xpath('./a/text()').extract_first() for i in range(len(breadcrumbs))}
        brand = response.xpath("//td[contains(@data-th,'rand')]/text()").extract_first()
        default_old_price = price_boxes[0].xpath('..//div[@class="old-price"]//span/text()').extract_first()
        default_price = price_boxes[0].xpath('..//span[@class="price"]/text()').extract_first()
        default_dict = {
                    'Date': datetime.now().strftime("%Y-%m-%d"),
                    'Canal': 'Scorpion',
                    'Category': breadcrumbs_dict.get(0, ''),
                    'Subcategory': breadcrumbs_dict.get(1, ''),
                    'Subcategory2': breadcrumbs_dict.get(2, ''),
                    'Subcategory3': '',
                    'Marca': brand,
                    'Modelo': '',
                    'SKU': sku,
                    'UPC': sku,
                    'Item': item,
                    'Item Characteristics': item_characteristics,
                    'URL SKU': response.url,
                    'Image': image,
                    'Price': '',
                    'Sale Price': '',
                    'Shipment Cost': '',
                    'Sales Flag': '',
                    'Store ID': '',
                    'Store Name': '',
                    'Store Address': '',
                    'Stock': '',
                    'UPC WM': sku.zfill(16),
                    'Final Price': '',
                    }
        for price_box in price_boxes:
            model = price_box.xpath('.//label/h4/text()').extract_first()
            price = price_box.xpath('.//span[@class="price"]/text()').extract_first()
            old_price = price_box.xpath('//div[@class="old-price"]//span/text()').extract_first()
            remainig_models = price_box.xpath('.//h4//sub/text()').extract()
            if old_price:
                temp_price = old_price
                old_price = price
                price = temp_price
            if not remainig_models:
                default_dict_copy = default_dict.copy()
                default_dict_copy['Modelo'] = model
                default_dict_copy['Price'] = self.filter_price(price)
                default_dict_copy['Sale Price'] = self.filter_price(old_price)
                default_dict_copy['Final Price'] = min(default_dict_copy['Price'], default_dict_copy['Sale Price']) if default_dict_copy['Sale Price'] else default_dict_copy['Price']
                yield default_dict_copy
            if remainig_models:
                models = price_box.xpath('.//h4//sub/text()').extract()
                sales_flag = price_box.xpath('.//span[@class="labelnew"]/text()').extract()
                sale_price = price_box.xpath('.//div[@class="price"]/text()').extract()
                for model, sale_flag, sale_price in zip(models, sales_flag, sale_price):
                    default_dict_copy = default_dict.copy()
                    default_dict_copy['Modelo'] = model
                    default_dict_copy['Sales Flag'] = sale_flag
                    default_dict_copy['Price'] = self.filter_price(default_old_price) if default_old_price else self.filter_price(default_price)
                    default_dict_copy['Sale Price'] = self.filter_price(sale_price)
                    default_dict_copy['Final Price'] = min(default_dict_copy['Price'], default_dict_copy['Sale Price']) if default_dict_copy['Sale Price'] else default_dict_copy['Price']
                    yield default_dict_copy
                    yield default_dict_copy
