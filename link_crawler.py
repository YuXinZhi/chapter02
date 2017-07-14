import re
import urllib.request
import urllib.parse
from datetime import datetime
import time
import urllib.robotparser

def link_crawler(seed_url,link_regex=None,delay=5,max_depth=1,max_urls=1,headers=None,
                 user_agent='wswp',proxy=None,num_retries=1,scrape_callback=None):
    '''crawl from the given seed URL following links matched by link_regex
    '''
    # the queue of URL's that still need to be crawled
    crawl_queue = [seed_url]
    # the URL's that have been seen and at what depth
    seen = {seed_url:0}
    # track how many URL's have been downloaded
    num_urls = 0
    rp = get_robots(seed_url)
    throttle = Throttle(delay)
    headers= headers or {}
    if user_agent:
        headers['User-agent'] = user_agent

    while crawl_queue:
        url = crawl_queue.pop()
        depth = seen[url]
        # check url passes robots.txt restrictions
        if rp.can_fetch(user_agent,url):
            throttle.wait(url)
            html = download(url,headers,proxy=proxy,num_retries=num_retries)
            links = []
            if scrape_callback:
                links.extend(scrape_callback(url,html) or [])

            if depth != max_depth:
                # can still crawl further
                if link_regex:
                    #filter for links matching our regular expression
                    links.extend(link for link in get_links(html) if re.match(link_regex,link))

                for link in links:
                    link = normlize(seed_url,link)
                    # check whether already crawled this link
                    if link not in seen:
                        seen[link] = depth + 1
                        # check link is within same domain
                        if same_domain(seed_url,link):
                            # success! add this new link to queue
                            crawl_queue.append(link)

            #check whether have reached downloaded maximum
            num_urls +=1
            if num_urls == max_urls:
                break
        else:
            print('Blocked by robots.txt',url)



class Throttle(object):
    '''Throttle downloading by sleeping between downloads for each domain
    '''
    def __init__(self,delay):
        # amount of delay between downloads for each dimain
        self.delay = delay
        # timestamp of when a domain was last accessed
        self.domains = {}

    def wait(self,url):
        '''delay if have accessed this domain recently
        '''
        domain = urllib.parse.urlsplit(url).netloc
        last_accessed = self.domains.get(domain)
        if self.delay > 0:
            sleep_secs = self.delay - (datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.now()

def get_robots(url):
    '''Initialize robots parser for the domain
    '''
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urllib.request.urljoin(url,'/robots.txt'))
    rp.read()
    return rp


def download(url,headers,proxy,num_retries,data=None):
    print('Downloading:',url)
    request = urllib.request.Request(url,data,headers)
    opener = urllib.request.build_opener()
    if proxy:
        proxy_params = {urllib.parse.urlparse(url).scheme:proxy}
        opener.add_handler(urllib.request.ProxyHandler(proxy_params))
    try:
        response = opener.open(request)
        html = response.read()
        code = response.code
    except urllib.URLError as e:
        print('Download error:',e.reason)
        html = ''
        if hasattr(e,'code'):
            code = e.code
            if num_retries > 0 and 500 <= code <600:
                # retry 5XX HTTP errors
                html = download(url,headers,proxy,num_retries-1,data)
            else:
                code = None
    return html


def get_links(html):
    '''Return a list of links from html
    '''
    # a regular expression to extract all link from the webpage
    webpage_ragex = re.compile('<a[^>]=href=["\'](.*?)["\']',re.IGNORECASE)
    html = html.decode('utf-8')
    # list if all links from the webpage
    return webpage_ragex.findall(html)

def normlize(seed_url,link):
    '''Normalize this URL by removing hash ans adding domain
    '''
    link, _ =urllib.parse.urldefrag(link)   #remove hash to avoid duplicates
    return urllib.parse.urljoin(seed_url,link)

def same_domain(url1,url2):
    '''Return True if both URL's belong to same domain
    '''
    return urllib.parse.urlparse(url1).netloc == urllib.parse.urlparse(url2).netloc

if __name__ == '__main__':
    link_crawler('http://example.webscraping.com/places','/(index|view)',delay=0,num_retries=1,user_agent='BadCrawler')
    link_crawler('http://example.webscraping.com','/(index|view)',delay=0,num_retries=1,max_depth=1,user_agent='GoodCrawler')