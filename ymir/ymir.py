#!/usr/bin/env python
# encoding: utf-8
"""
Code for managing la-grange.net.

Created by Karl Dubost on 2011-12-03.
Copyright (c) 2011 Grange. All rights reserved.
see LICENSE.TXT
"""

import argparse
import configparser
from dataclasses import dataclass
import datetime
import logging
import os
import shutil
import string
from io import StringIO
import sys

from lxml import etree
from lxml.etree import Element
from lxml.etree import SubElement
import lxml.html

from ymir.utils import helper
from ymir.utils import parsing
from ymir.utils import feed

# from tracer import show_guts

# CONFIG SITE
config = configparser.ConfigParser()
config.read('blog.cfg')

HTMLNS = "http://www.w3.org/1999/xhtml"
HTML = "{%s}" % HTMLNS
NSMAP = {None: HTMLNS}
NSMAP3 = {'html': HTMLNS}

ATOMNS = "http://www.w3.org/2005/Atom"
NSMAP2 = {None: ATOMNS}
ATOM = "{%s}" % ATOMNS
NSMAP4 = {'atom': ATOMNS}

LICENSELIST = {'ccby': 'http://creativecommons.org/licenses/by/2.0/fr/',
               'copy': '©'}

DOMAIN = "la-grange.net"
SITE = "http://www.%s/" % (DOMAIN)
ROOT_TOKEN = 'tagid-2000-04-12'
FAVICON = SITE + "favicon"
CODEPATH = os.path.dirname(sys.argv[0])
TEMPLATEDIR = CODEPATH + "/../templates/"

SITENAME = "Les carnets Web de La Grange"
TAGLINE = "Rêveries le long d'un brin de chèvrefeuille"

FEEDTAGID = "tag:la-grange.net,2000-04-12:karl"
FEEDLANG = "fr"
FEEDATOMNOM = "feed.atom"
FEEDATOMURL = "%s%s" % (SITE, FEEDATOMNOM)
FEED_MAX_POSTS = 25

STATUSLIST = ['draft', 'pub', 'acl']
DATETYPELIST = ['created', 'modified']
LICENSELIST = {'ccby': 'http://creativecommons.org/licenses/by/2.0/fr/',
               'copy': '©'}

AUTHOR = "Karl Dubost"
AUTHORURI = "http://www.la-grange.net/karl/"

HTMLNS = "http://www.w3.org/1999/xhtml"
HTML = "{%s}" % HTMLNS
NSMAP = {None: HTMLNS}
NSMAP3 = {'html': HTMLNS}

# CONFIG with cli
STYLESHEET = "/2011/12/01/proto/style/article.css"
STATUS = ""
MAXFEEDITEM = 20
LICENSE = "ccby"

date_now = datetime.datetime.today()

# PATHS

help_message = """
This script has been entirely created
for processing text files for the site
La Grange http://www.la-grange.net/.
"""


def update_home_index(feed_path, home_path, id_name):
    """Update the HTML index with the feedendry content."""
    # Get HTML from the index
    if os.path.isfile(home_path):
        html = lxml.html.parse(home_path)
        home = html.getroot()
    else:
        logging.error("WRONG PATH: %s" % (home_path))
    # Get an entry dictionary from the Feed
    entries = last_posts(feed_path)
    # Generate string with markup
    home_template = """<ul id="{id}">
    {posts_list}
    </ul>
    """
    posts_list = last_posts_html(entries)
    home_index = home_template.format(
        id=id_name,
        posts_list=posts_list)
    lis = lxml.html.fragment_fromstring(home_index)
    # replace the content of the home index
    blog_ul = home.get_element_by_id(id_name)
    blog_ul.getparent().replace(blog_ul, lis)
    return lxml.html.tostring(html, encoding='utf-8')


def updatemonthlyindex(indexmarkup, monthindexpath):
    """Update the HTML monthly index with the feedendry."""
    # Looking for a monthly index
    if os.path.isfile(monthindexpath):
        monthlyindex = lxml.html.parse(monthindexpath).getroot()
        logging.info("Monthly Index exists")
    else:
        logging.warn("Monthly index doesn’t exist. TOFIX")
        createmonthlyindex(monthindexpath)
    # grab the list of entry
    print((etree.tostring(indexmarkup), monthindexpath))
    findentrylist = etree.ETXPath("//section[@id='month-index']/ul/li")
    entries = findentrylist(monthlyindex)
    # search
    find_href = etree.ETXPath("a/@href")
    find_created = etree.ETXPath("time/@datetime")
    find_title = etree.ETXPath("a/text()")
    # Reference
    href_ref = find_href(indexmarkup)[0]
    created_ref = find_created(indexmarkup)[0]
    title_ref = find_title(indexmarkup)[0]
    entry_ref = {
        'href': href_ref,
        'created': created_ref,
        'title': title_ref}
    print(entry_ref)
    # Index data
    monthly_entries = []
    for entry in entries:
        href_entry = find_href(entry)[0]
        # same URI, entry already exists, we stop.
        if href_entry == href_ref:
            return False
        created_entry = find_created(entry)[0]
        title_entry = find_title(entry)[0]
        entry_data = {
            'href': href_entry,
            'created': created_entry,
            'title': title_entry}
        monthly_entries.append(entry_data)
    # sorted_entries = sorted(monthly_entries,
    #                         key=lambda entry: entry['created'])
    LI_TEMPLATE = '<li><time class="created" datetime="{date}">{date_short}</time> : <a href="{href}">{title}</a></li>'  # noqa
    html_markup = [
        LI_TEMPLATE.format(
            date=entry['created'],
            date_short=entry['created'][:10],
            href=entry['href'],
            title=entry['title']
        )
        for entry in monthly_entries]
    return '\n'.join(html_markup)


def createindexmarkup(postpath, created, title):
    """Create the Markup necessary to update the indexes."""
    dcreated = {'class': 'created', 'datetime': created}
    # Creating the Markup
    # li = etree.Element("{%s}li" % HTMLNS, nsmap=NSMAP)
    li = etree.Element("li")
    ctime = etree.SubElement(li, 'time', dcreated)
    ctime.text = created[:10]
    ctime.tail = " : "
    anchor = etree.SubElement(li, 'a', {'href': postpath})
    anchor.text = title.strip()
    return li


def createmonthlyindex(indexmarkup, monthindexpath):
    """Create a monthly index when it doesn't exist."""
    # Code ici pour lire un fichier avec des variables
    # substituer les variables par les valeurs du mois
    # sauver le fichier au bon endroit
    msg = "Do not forget to update /map with your tiny hands"
    logging.info("%s" % (msg))

    with open(TEMPLATEDIR + 'index-mois.html', 'r') as source:
        t = string.Template(source.read())
        datestring = helper.convert_date(date_now, 'iso')
        datehumain = helper.convert_date(date_now, 'humain')
        # to get month, we split in 3 the human date and take the second
        # argument
        datemois = datehumain.split(' ')[1]
        indexli = etree.tostring(
            indexmarkup, pretty_print=True, encoding='utf-8')
        result = t.substitute(isodateshort=datestring,
                              monthname=datemois,
                              year=datestring[:4],
                              humandate=datehumain,
                              firstentry=indexli)
        # need to write it on the filesystem.
    with open(monthindexpath, 'w') as monthindex:
        monthindex.write(result)


def last_posts(feed_path):
    """Create a list of dictionaries of the last posts using the Atom feed."""
    entries = []
    feed_root = helper.parse_feed(feed_path)
    # Information we need: title, dates, link
    find_entry = etree.ETXPath("//{%s}entry" % ATOMNS)
    find_title = etree.ETXPath("{%s}title/text()" % ATOMNS)
    find_published = etree.ETXPath("{%s}published/text()" % ATOMNS)
    find_updated = etree.ETXPath("{%s}updated/text()" % ATOMNS)
    # Only the link pointing to the blog post
    find_url = etree.ETXPath("{%s}link[@rel='alternate']/@href" % ATOMNS)
    # Extract all the entries
    feed_entries = find_entry(feed_root)
    # We iterate through them
    for entry in feed_entries:
        entry_data = {'title': find_title(entry)[0],
                      'published': find_published(entry)[0],
                      'updated': find_updated(entry)[0],
                      'url': find_url(entry)[0]}
        entries.append(entry_data)
    return entries


def last_posts_html(entries):
    """Return the HTML markup for the last entries."""
    # msg = "Generating HTML markup for last entries in the feed"
    # logging.info("%s" % (msg))
    last_posts_markup = ''
    with open(TEMPLATEDIR + 'last_posts.html', 'r') as source:
        t = string.Template(source.read())
        for entry in entries:
            published = entry['published']
            tshortdate = published[:10]
            last_posts_markup += t.substitute(
                ttitle=entry['title'].encode('utf-8'),
                turl=entry['url'],
                tpublished=published,
                tshortdate=tshortdate)
    return last_posts_markup


# MAIN
def main():
    """Run the core task for processing a file for La Grange."""
    # Logging File Configuration
    logging.basicConfig(filename='log-ymir.txt', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('-' * 80)
    # Command Line Interface
    parser = argparse.ArgumentParser(
        description="Managing Web site blog posts")
    parser.add_argument('rawpost', metavar='FILE', help='file to be processed',
                        action='store', nargs=1, type=argparse.FileType('rt'))
    parser.add_argument('-t', '--testmode', action='store_true',
                        help='Run ymir without writing files.')
    args = parser.parse_args()
    # Mode for testing the code without destroying the files
    dryrun = False
    if args.testmode:
        dryrun = True
    # Arguments attribution
    raw_post_path = args.rawpost[0]

    # *** PATH CONFIGURATIONS ***
    # Getting the path of the current post on the OS
    abspathpost = os.path.abspath(raw_post_path.name)
    post_directory = os.path.dirname(abspathpost)
    # Finding the root of the Web site
    site_root = helper.find_root(post_directory, ROOT_TOKEN)
    logging.info('site root: {root}'.format(root=site_root))
    # Post path and full URL without ".html"
    postpath = abspathpost[len(site_root):]
    logging.info('post path: {path}'.format(path=postpath))
    posturl = "%s%s" % (SITE[:-1], postpath[:-5])
    logging.info('post url: {url}'.format(url=posturl))
    # Feed
    feed_path = '%s/%s' % (site_root, FEEDATOMNOM)
    logging.info('feed path: {path}'.format(path=feed_path))
    # Site Home Page
    home_path = '%s/%s' % (site_root, 'index.html')
    logging.info('home_path: {path}'.format(path=home_path))
    # Monthly index
    monthabspath = os.path.dirname(os.path.dirname(abspathpost))
    logging.info('month absolute path: {path}'.format(path=monthabspath))
    monthindexpath = monthabspath + "/index.html"
    logging.info('month index path: {path}'.format(path=monthindexpath))
    # *** END PATH CONFIGURATIONS ***

    # *** BACKUPS ***
    # preparing places for backup
    backup_path = '/tmp/lagrange'
    if not os.path.isdir(backup_path):
        os.mkdir(backup_path)
    feed_path_bkp = '%s/%s' % (backup_path, FEEDATOMNOM)
    shutil.copy(feed_path, feed_path_bkp)
    # *** PROCESSING ***
    # Parse the document
    rawpost = helper.parse_raw_post(raw_post_path)
    # Extracting Post Information
    title = parsing.get_title(rawpost)
    title = title.strip()
    logging.info("TITLE: %s" % (title))
    created = parsing.get_date(rawpost, 'created')
    logging.info("CREATED: %s" % (created))
    modified = parsing.get_date(rawpost, 'modified')
    date_now = helper.rfc3339_to_datetime(modified)
    logging.info("MODIFIED: %s" % (modified))
    # the content of the article, we can do better
    content = parsing.get_content(rawpost)

    # INDEX MARKUP
    indexmarkup = createindexmarkup(postpath[:-5], created, title)

    # MONTHLY INDEX CREATION
    # Create the monthly index if it doesn't exist yet
    # Happen once a month
    if not os.path.isfile(monthindexpath):
        createmonthlyindex(indexmarkup, monthindexpath)
    else:
        # TOFIX: updating the monthly index
        # UPDATE THE MONTHLY INDEX
        if not dryrun:
            html_markup = updatemonthlyindex(indexmarkup, monthindexpath)
            print('WE should write to the index')
            print(html_markup)
            print((etree.tostring(
                indexmarkup, pretty_print=True, encoding='unicode')))
        else:
            print('TESTING - This would be written:')
            html_markup = updatemonthlyindex(indexmarkup, monthindexpath)
            if not html_markup:
                print('nothing to write. Index is already up to date')
            else:
                print(html_markup)
            print(('-' * 80))
            print((etree.tostring(
                indexmarkup, pretty_print=True, encoding='utf-8')))

    # FEED ENTRY MARKUP
    # We compute the tagid using the creation date of the post
    created_dt = helper.rfc3339_to_datetime(created)
    created_iso = helper.convert_date(created_dt, 'iso')
    tagid = helper.create_tagid(posturl, created_iso)
    # UPDATING FEED
    feedentry_data = {'url': posturl,
                      'tagid': tagid,
                      'title': title,
                      'created': created,
                      'modified': helper.convert_date(date_now, 'rfc3339'),
                      'content': content}
    feedentry = feed.makefeedentry(feedentry_data)
    feed_content = feed.update_feed(feedentry, feed_path_bkp)

    # SAVE ATOM FEED
    if feed_content:
        if not dryrun:
            with open(feed_path, 'w') as feedbkp:
                feedbkp.write(feed_content.decode('utf-8'))
        else:
            print('TESTING: feedbkp.write(feed_content)')
            print(feed_content)

    # UPDATING HOME PAGE
    home_content = update_home_index(feed_path, home_path, 'posts_list')
    if not dryrun:
        pass
        # todo
        # with open(home_path, 'w') as home:
        #     home.write(home_content.decode('utf-8'))
    else:
        print('TESTING: home.write(home_content)')
    # UPDATING MONTHLY INDEX
    # updatemonthlyindex(indexmarkup, monthindexpath)


if __name__ == "__main__":
    main()
