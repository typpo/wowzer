#!/usr/bin/env python

import os
import sys
import simplejson
import urllib, urllib2
import datetime
import gzip
import json
from StringIO import StringIO
from time import time

import db
import util
import arbitrage as arb
from money import Money

REALMS_DIR = '/home/ian/projects/wowzer/realms/%s/%s'
REALMS_BASE = 'http://%s.battle.net/api/wow/realm/status'
AUCTIONS_CHECK = 'http://%s.battle.net/api/wow/auction/data/%s'

TEST = ('us', 'elune', 'a')

def updateRealms(country):
    # Get realms list and create corresponding directories if applicable
    print 'Refreshing realm data'
    if not os.path.isdir(REALMS_DIR % (country)):
        os.mkdir(REALMS_DIR % (country))
    j = simplejson.load(urllib.urlopen(REALMS_BASE % (country)))
    ret = []
    for realm in j['realms']:
        dir = os.path.join(REALMS_DIR % (country), realm['slug']).encode('utf-8')
        ret.append(realm['slug'])
        if not os.path.isdir(dir):
            os.mkdir(dir)

    return ret

def updateData(country, slugs):
    # Record auction data
    c = 1
    for slug in slugs:
        print 'Processing %s records (%d of %d)' % (slug, c, len(slugs))
        try:
            # Check for modifications
            status = simplejson.load(urllib.urlopen(AUCTIONS_CHECK % (country, slug)))['files'][0]

            info = os.path.join(REALMS_DIR % (country, slug), 'info')

            # Someday this will be a config file, maybe
            modified = 0
            if os.path.exists(info):
                f = open(info, 'r')
                lines = f.readlines()
                if len(lines) > 0:
                    modified = int(lines[0])
                f.close()

            if modified >= status['lastModified']:
                print '\t No update'
                continue

            f = open(info, 'w')
            f.write(str(status['lastModified']))
            f.close()

            # Download full auctions page - try gzip
            request = urllib2.Request(status['url'])
            request.add_header('Accept-encoding', 'gzip')
            response = urllib2.urlopen(request)
            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                data = f.read()
            else:
                print '%s-%s not gzipped' % (country, slug)
                data = response
            j = simplejson.loads(data)
        except:
            print 'Error loading %s-%s' % (country, slug)
            continue

        def process(aucs, side):
            db.insertAuctions((country, slug, side), aucs['auctions'])
            print '\t%s: %d' % (side, len(aucs['auctions']))

            writeme = json.dumps(arb.findCraftable((country,slug,side)))
            arbitrage_file = os.path.join(REALMS_DIR % (country, slug), 'arb_'+side)
            f = open(arbitrage_file, 'w')
            f.write(writeme)
            f.close()

        process(j['alliance'], 'a')
        process(j['horde'], 'h')
        process(j['neutral'], 'n')
        c+=1

    
def updateAll():
    eu_realms = updateRealms('eu') 
    updateData('eu', eu_realms)
    us_realms = updateRealms('us') 
    updateData('us', us_realms)


def updateTest():
    updateData('us', ['elune'])
    
    
def main():
    print str(datetime.datetime.now())

    if len(sys.argv) == 2 and sys.argv[1] == 'dev':
        print 'dev mode'
    else:
        updateTest()

if __name__ == '__main__':
    main()
