import logging
import os
import re
import json

from datetime import date, datetime
from urllib import urlencode
from urllib2 import urlopen
from time import time
from xml.etree import ElementTree

# only consider books from those three shelves
SHELVES = ['read', 'currently-reading', 'to-read']
DAY = 86400  # 24h in seconds


def api_endpoint_url(key, user_id, page=1):
    """Construct API endpoint for getting user's list of books."""
    endpoint = 'https://www.goodreads.com/review/list/'
    query_args = {
        'key': key,       # goodread's api key
        'format': 'xml',  # this endpoing only supports xml
        'id': user_id,
        'v': 2,           # api version (defaults to 1)
        'per_page': 200,  # maximum for that value
        'page': page
    }
    return '{}?{}'.format(endpoint, urlencode(query_args))


def extract_authors(book):
    """Given book extract list of the authors."""
    authors = []
    for author in book.findall('.//author'):
        authors.append(author.find('name').text)
    return ', '.join(authors)


def parse_date(xml_datetime):
    """Parse goodread's date into datetime object."""
    if not xml_datetime:
        return None

    # remove timezone info, because python can't properly parse it, at least
    # not without installing additional libraries
    xml_datetime = re.sub(r' (-|\+)?\d{4} ', ' ', xml_datetime)

    return datetime.strptime(xml_datetime, '%a %b %d %H:%M:%S %Y')


def extract_shelf(review):
    """Given review return one of the three possible shelves or None."""
    shelves = [shelf.attrib['name'] for shelf in review.find('shelves')]
    shelves = filter(lambda shelf: shelf in SHELVES, shelves)

    if shelves:
        return shelves[0]
    else:
        return None


def date_grouppings(date_read):
    """Extract date grouppings for given date."""
    if date_read:
        year = date_read.year
        month = date_read.date().replace(day=1)
    else:
        year = None
        month = None

    return year, month


def extract_book_info(tree):
    """Given goodread's API response extract book info."""
    infos = []
    for review in tree.findall('.//review'):
        book = review.find('book')
        rating = book.find('rating')

        date_read = parse_date(review.find('read_at').text)
        year, month = date_grouppings(date_read)

        infos.append({
            'title': book.find('title').text,
            'authors': extract_authors(book),
            'date': date_read,
            'year': year,
            'month': month,
            'link': book.find('link').text,
            'rating': int(rating) if rating else 0,
            'shelf': extract_shelf(review),
        })
    return infos


def extract_pagination_info(tree):
    """Given goodread's API response extract pagination info."""
    reviews_tag = tree.find('reviews')

    # if those attributes are not integers, there's more serious problem
    start = int(reviews_tag.attrib['start'])
    end = int(reviews_tag.attrib['end'])
    total = int(reviews_tag.attrib['total'])

    return start, end, total


def user_books(key, user_id):
    """Return list of dictionaries describing user's books."""
    page = 1
    books = []

    # there may be more than one page of the results
    while True:
        response = urlopen(api_endpoint_url(key, user_id, page), timeout=60)
        xml_data = response.read()
        xml = ElementTree.fromstring(xml_data)

        books.extend(extract_book_info(xml))

        _, end, total = extract_pagination_info(xml)
        # did we reach the end of the pages?
        if end == total:
            break

        page += 1

    return books


def should_update_local_file(path, interval):
    """Check if books file is old enough to be updated."""
    if os.path.exists(path):
        mtime = os.stat(path).st_mtime
        # abs is for a weird case of filesystem times being in the future
        difference = abs(time() - mtime)
        return difference >= interval
    else:
        return True


def serialize_datetime(obj):
    """Serialize datetime object to string."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    else:
        raise TypeError


def unisoformat(s):
    """Turn result of .isoformat() back into datetime."""
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')


def deserialize_datetime(d):
    """Deserializes values of fields named `date`."""
    if 'date' in d and d['date']:
        d['date'] = unisoformat(d['date'])

    return d


def books_on_shelf(books, shelf):
    return [b for b in books if b['shelf'] == shelf]


def preBuildPage(page, context, data):
    key = page.site.config.get('goodreads-key')
    if not key:
        logging.warn("No goodreads API key found!")
        return context, data

    user_id = page.site.config.get('goodreads-user-id')
    if not user_id:
        logging.warn("No goodreads user id found!")
        return context, data

    interval = page.site.config.get('goodreads-refresh-interval')
    # default to one update every 24h
    if interval is None:
        interval = DAY

    data_path = os.path.join(page.site.path, 'books.json')
    if should_update_local_file(data_path, interval):
        books = user_books(key, user_id)
        with open(data_path, 'w') as output:
            # pretty print json, so it's user viewable
            json.dump(books, output, indent=2, default=serialize_datetime)

    books = json.load(open(data_path), object_hook=deserialize_datetime)

    context['books'] = books
    context['books_read'] = books_on_shelf(books, 'read')
    context['books_reading'] = books_on_shelf(books, 'currently-reading')
    context['books_to_read'] = books_on_shelf(books, 'to-read')

    return context, data
