"""
chkurls.py - check urls in a text stream work.

Terry N. Brown terrynbrown@gmail.com Fri Mar 15 13:08:21 EDT 2019
"""

import json
import os
import re
import sys
import time

import requests

URL_RE = (
    'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|'
    '[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)
CACHE = ".url.chl.json"
GOOD_RESPONSE = 200, 302

if os.path.exists(CACHE):
    cache = json.load(open(CACHE))
else:
    cache = {'url': {}}
seen = set()
search = re.compile(URL_RE)


def get_urls(stream):
    for line_n, line in enumerate(stream):
        for match in search.finditer(line):
            yield line_n, match.group()


now = time.time()
min_time = now - 90 * 24 * 60 * 60


def get_status_code(to_try):
    for url in to_try:
        try:
            r = requests.head(url, verify=False)
            status_code = r.status_code
        except requests.exceptions.ConnectionError:
            print("  ConnectionError")
            status_code = 0
        if status_code in GOOD_RESPONSE:
            break
    return status_code


for line_n, url in get_urls(sys.stdin):
    if url in seen:
        continue
    seen.add(url)
    if url not in cache['url']:
        cache['url'][url] = {'time': now, 'ok': False}
    info = cache['url'][url]
    if info['time'] > min_time and info['ok'] is True:
        continue
    to_try = [url]
    if url[-1] in '.,;':
        to_try.append(url[:-1])
    status_code = get_status_code(to_try)
    if status_code in GOOD_RESPONSE:
        info['ok'] = True
        info['time'] = now
    else:
        print(url)
        info['ok'] = False
        print("  %s status %s" % (url, status_code))

with open(CACHE, 'w') as out:
    json.dump(cache, out)
