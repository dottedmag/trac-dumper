#!/usr/bin/env python

import errno
import os
import os.path
import re
import requests
from bs4 import BeautifulSoup as BS

def includer(exclude, include):
    def do(link):
        for regex in include:
            if regex.match(link):
                return True
        for regex in exclude:
            if regex.match(link):
                return False
        return True
    return do

def pages(baseurl, includer):
    r = requests.get(baseurl + '/wiki/TitleIndex')
    soup = BS(r.text)
    index = soup.find("div", {"class": "titleindex"})
    for a in index.find_all("a"):
        link = a['href'].replace('/wiki/', '')
        if includer(link):
            yield link


def link_to(from_page, to):
    if to.startswith('http://openinkpot.org'):
        to = to[21:]
    return to
    #if to.startswith('http') or to.startswith('ftp') or to.startswith('#'):
    #    return to
    #assert to.startswith('/')
    #level = from_page.count('/')
    #return '..' + ('/..' * level) + to

def remove_elems(soup, elems):
    for prop, tags in elems.iteritems():
        for tagname, ids in tags.iteritems():
            for id in ids:
                for elem in soup.find_all(tagname, {prop: id}):
                    if not elem:
                        print "Can't find <{0} {1}='{2}'>".format(tagname, prop, id)
                    else:
                        elem.clear()

# FIXME: change CSS for #header img margin
def clean_page(baseurl, page):
    r = requests.get(baseurl + '/wiki/' + page)
    soup = BS(r.text)
    remove_elems(soup, {"id": {"div": ["footer", "metanav",
                                       "ctxtnav", "altlinks"], "form": ["search"]},
                        "class": {"div": ["trac-modifiedby"]},
                        "rel": {"link": ["search", "alternate"]}})
    mainnav = soup.find('div', id="mainnav")
    lis = mainnav.ul.find_all('li')
    lis[3].clear()
    lis[2].clear()
    lis[1].clear()
    for elem in soup.find_all(href=True):
        elem['href'] = link_to(page, elem['href'])
    for elem in soup.find_all(src=True):
        elem['src'] = link_to(page, elem['src'])
    for script in soup.find_all('script', {'type': 'text/javascript'}):
        if script.string and script.string.find('tracnav.css'):
            script.string = script.string.replace('/chrome/tracnav/css/tracnav.css',
                link_to(page, '/chrome/tracnav/css/tracnav.css'))
    return soup.prettify()

for page in pages('http://openinkpot.org/', includer([re.compile('.*\/(cs|da|de|el|es|fr|hu|ja|nl|pl|pt|ru|sv|uk|zh|tmp|temp)$'), re.compile('^(Wiki|Trac|PageTemplates|Inter).*'), re.compile('^(RecentChanges|SandBox|TitleIndex|Donations)$')], [re.compile('Wiki(License|Start)$')])):
    print page
    cp = clean_page('http://openinkpot.org/', page)
    filename = os.path.join('out', 'wiki', page)
    dirname = os.path.dirname(filename)
    if dirname:
        try:
            os.makedirs(dirname)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
    with open(filename+'.html', 'w') as fh:
        fh.write(cp.encode('UTF-8'))
