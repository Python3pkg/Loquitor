import ast
import csv
import html
from io import StringIO
import json
import operator as op
import re

from bs4 import BeautifulSoup
import requests
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen


OPERATORS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

WIKI_DEFINE = 'en.wiktionary.org'
WIKI_ENCYCL = 'en.wikipedia.org'

def search_bing(q, results=5, **kwargs):
    kwargs['q'] = q
    url = "https://bing.com/search?" + urlencode(kwargs)
    page = urlopen(url)
    soup = BeautifulSoup(page)

    # A tag that shows up before the search results
    tag = soup.find('title')
    for i in range(results):
        tag = tag.find_next('li', {'class': 'b_algo'})
        if tag is None:
            if i == 0:
                raise StopIteration
            else:
                yield from search_bing(q, results - i, first=i)
                break

        title_tag = tag.find('h2').find('a')
        title = title_tag.text
        url = title_tag['href']
        info = tag.find('p').text
        yield title, url, info

def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return OPERATORS[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return OPERATORS[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

def on_search(event, room, client, bot):
    search = search_bing(event.query)
    messages = []

    format = "> {title}, ({url})\n\n{desc}"

    for title, url, desc in search:
        messages.append(format.format(title=title, url=url, desc=desc))

    event.message.reply("\n\n\n".join(messages), False)

def on_xkcd(event, room, client, bot):
    query = event.query
    if query.isdigit():
        event.message.reply("https://xkcd.com/" + query)
    else:
        search = search_bing('site:xkcd.com ' + query, 1)
        try:
            event.message.reply(next(search)[1])
        except StopIteration:
            event.message.reply("Woops.  It looks like I couldn't that.")

def wiki_find(event, room, client, bot, site=WIKI_ENCYCL):
    url = "https://{}/w/index.php?search={}".format(site, quote_plus(event.query))
    r = requests.get(url)
    if r.url.startswith("https://{}/wiki".format(site)):
        event.message.reply(r.url)
        return

    page = BeautifulSoup(r.text)

    did_you_mean = page.find('div', {'class': 'searchdidyoumean'})
    if did_you_mean:
        link = did_you_mean.find('a')['href']
        link_regex = '&search=(?P<word>.*?)&'
        word = re.search(link_regex, link).group('word')
        event.query = word
        wiki_find(event, room, client, site)
        return

    first_result = page.find("div", {'class': 'mw-search-result-heading'})
    if first_result:
        link = first_result.find('a')
        event.message.reply('https://{}{}'.format(site, link['href']))
        return

    event.message.reply("Sorry, I don't know that word.")

def on_whatis(event, room, client, bot):
    query = event.query
    try:
        event.message.reply(eval_expr(query))
        return
    except (TypeError, SyntaxError):
        query = "define " + query

    url = "https://www.google.com/s?sclient=psy-ab"\
            "&site=&source=hp&q={}&oq=&gs_l=&pbx=1"\
            "&bav=on.2,or.r_cp.&bvm=bv.133700528,d.bGs"\
            "&fp=1&biw=734&bih=638&dpr=1&sns=1&pf=p"\
            "&tch=1&ech=9&psi=xT7pV7SOF-rO6ASN2o7gDA.1474903753059.1"\
            .format(quote_plus(query))

    response = requests.get(url)

    resp_json_text = response.text
    resp_json_nodes = resp_json_text.split('/*""*/')[:-1]
    if len(resp_json_nodes) < 2:
        event.message.reply("Sorry, I just don't know.")
        return

    result_node = resp_json_nodes[1]
    result_json = json.loads(result_node)
    result_html = result_json.get('d')

    soup = BeautifulSoup(result_html)
    definition_tag = soup.find('div', {'class': '_o0d'})
    if definition_tag is None:
        event.command = 'define'
        event.data['command'] = 'define'
        wiki_find(event, room, bot, client, site=WIKI_DEFINE)
    else:
        event.message.reply(definition_tag.text)

def on_youtube(event, room, client, bot):
    query = event.query
    url = "https://youtube.com/results?search_query=" + quote_plus(query)
    html = urlopen(url)
    soup = BeautifulSoup(html)
    result = soup.find('h3', {'class': 'yt-lockup-title'})
    if result is None:
        event.message.reply("Sorry, no results found.")
    else:
        link = result.find('a')['href']
        while not link.startswith('/watch'):
            result = result.findNext('h3', {'class': 'yt-lockup-title'})
            link = result.find('a')['href']

        event.message.reply("https://youtube.com" + link)

commands = {'search': on_search, 'wiki': wiki_find, 'youtube': on_youtube,
            'define': lambda e,r,c,b: wiki_find(e,r,c,b,WIKI_DEFINE),
            'yt': on_youtube, 'whatis': on_whatis, 'xkcd': on_xkcd,
}

help = {
    'search': 'Search for item on the web (using Bing)',
    'wiki': 'Search for item on Wikipedia',
    'define': 'Search for meaning of word (on Wiktionary)',
    'youtube': 'Search for item on YouTube',
    'yt': 'Synonym for `youtube`',
    'whatis': 'Find definition off of Google.  If nothing is found, use >>define',
    'xkcd': 'Search xkcd.com for a comic.  Can be given an id or a search term.',
}
