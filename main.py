#!/usr/bin/env python

import os
import sys
import simplejson
import urllib, urllib2
import datetime
import gzip
from StringIO import StringIO
from time import time

import db

REALMS_DIR = '/home/ian/projects/wowzer/realms/%s/%s'
REALMS_BASE = 'http://%s.battle.net/api/wow/realm/status'
AUCTIONS_CHECK = 'http://%s.battle.net/api/wow/auction/data/%s'

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
            f = open(info, 'r+')
            lines = f.readlines()
            modified = int(lines[0]) if len(lines) > 0 else 0

            if modified >= status['lastModified']:
                # No update
                print '\t No update'
                #f.close()
                #continue

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
        except IOError:
            print 'Error loading %s-%s' % (country, slug)
            continue

#        t = int(time())
        def process(aucs, side):
            """
            base = os.path.join(REALMS_DIR % (country, slug), str(t))
            if not os.path.isdir(base):
                os.mkdir(base)
            f = open(os.path.join(base, side), 'w')
            f.write(simplejson.dumps(aucs, separators=(',',':')))
            f.close()
            """

            db.insertAuctions((country, slug, side), aucs['auctions'])

            print '\t%s: %d' % (side, len(aucs['auctions']))

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
    #updateTest()

if __name__ == '__main__':
    main()
