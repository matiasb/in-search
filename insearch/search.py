#
# search.py
#
# Copyright (C) 2009 Matias Bordese <mbordese@gmail.com>
#

import json
import urllib2

from urllib import urlencode, quote

def isohunt_search(q):
    """Perform isoHunt torrents search."""
    # http://ca.isohunt.com/forum/viewtopic.php?p=433527&sid=#433527
    search_params = {'ihq': q,
                     'rows': '10',
                     'sort': 'seeds'}
    encoded_params = urlencode(search_params)

    api_url = 'http://isohunt.com/js/json.php?%s' % encoded_params
    url_data = urllib2.urlopen(api_url)
    data = json.load(url_data)

    results = []
    items = data.get('items', {}).get('list', [])
    for result in items:
        row = {'title': result['title'],
               'seeds': int(result['Seeds']),
               'leechers': int(result['leechers']),
               'size': result['size'],
               'url': result['enclosure_url'],
               'details_url': result['link']}
        results.append(row)
    return results
