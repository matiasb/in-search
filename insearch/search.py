#
# search.py
#
# Copyright (C) 2009 Matias Bordese <mbordese@gmail.com>
#

try:
    import json
except ImportError:
    import simplejson as json

#import urllib2

from twisted.internet import defer
from twisted.web import client
from urllib import urlencode, quote


@defer.inlineCallbacks
def isohunt_search(q, age=0):
    """Perform isoHunt torrents search."""
    # http://ca.isohunt.com/forum/viewtopic.php?p=433527&sid=#433527
    cookies = {'torrentAge': age}
    search_params = {'ihq': q,
                     'rows': '10',
                     'sort': 'seeds'}
    encoded_params = urlencode(search_params)

    api_url = 'http://isohunt.com/js/json.php?%s' % encoded_params
    #url_data = urllib2.urlopen(api_url)

    try:
        result = yield client.getPage(api_url, cookies=cookies)
    except:
        results = None
        defer.returnValue(results)
        
    data = json.loads(result)

    results = []
    items = data.get('items', {}).get('list', [])
    for result in items:
        try:
            seeds = int(result['Seeds'])
            leechers = int(result['leechers'])
        except ValueError:
            seeds = 0
            leechers = 0

        row = {'title': result['title'],
               'seeds': seeds,
               'leechers': leechers,
               'size': result['size'],
               'url': result['enclosure_url'],
               'pubDate': result['pubDate'],
               'votes': result['votes'],
               'details_url': result['link']}
        results.append(row)
    defer.returnValue(results)
