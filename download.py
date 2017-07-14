import urllib.request

def download(url,user_agent="wswp",proxy=None,num_retries=2):
    print("downloading : ", url)
    headers = {"user-agent": user_agent}
    urllib.request.Request(url, headers=headers)

    opener = urllib.request.build_opener()
    if proxy:
        proxy_params = {urllib.parse.urlparse(url).scheme: proxy}
        opener.add_handler(urllib.request.ProxyHandler(proxy_params))
    try:
        html = urllib.request.urlopen(url).read()
        html = html.decode('utf-8')  # python2和3兼容问题
    except urllib.request.URLError as  e:
        print("download error:", e.reason)
        html = None
        if num_retries > 0:
            if hasattr(e, "code") and 500 <= e.code < 600:
                # retry 5xx HTTP errors
                return download(url, user_agent, proxy, num_retries - 1)
    return html