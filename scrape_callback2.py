
import csv
import re
import lxml.html
from link_crawler import link_crawler
from bs4 import BeautifulSoup

class ScrapeCallback:
    def __init__(self):
        self.writer = csv.writer(open('countries.csv','w'))
        self.fields = ('area', 'population', 'iso', 'country', 'capital', 'continent', 'tld', 'currency_code', 'currency_name', 'phone', 'postal_code_format', 'postal_code_regex', 'languages', 'neighbours')
        self.writer.writerow(self.fields)

    def __call__(self, url, html):
        print('call')
        soup = BeautifulSoup(html, 'html.parser')
        print(soup.prettify())


        if re.search('/view/',url):
            tree = lxml.html.fromstring(html)
            row = []
            for field in self.fields:
                row.append(tree.cssselect('table > tr#places_{}__row > td.w2p_fw'.format(field))[0].text_content())
            print(row)
            self.writer.writerow(row)

if __name__ == '__main__':
    link_crawler('http://example.webscraping.com/', '/(index|view)',max_depth=-1, scrape_callback=ScrapeCallback())