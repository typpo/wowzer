#!/usr/bin/env python

import os
import sys
import simplejson
import urllib
from time import time

REALMS_DIR = 'realms/'
REALMS_BASE = 'http://us.battle.net/api/wow/realm/status'
AUCTIONS_BASE = 'http://us.battle.net/auction-data/%s/auctions.json'

def updateRealms():
    # Get realms list and create corresponding directories if applicable
    print 'Refreshing realm data'
    if not os.path.isdir(REALMS_DIR):
        os.mkdir(REALMS_DIR)
    j = simplejson.load(urllib.urlopen(REALMS_BASE))
    ret = []
    for realm in j['realms']:
        dir = os.path.join(REALMS_DIR, realm['slug']) 
        ret.append(realm['slug'])
        if not os.path.isdir(dir):
            os.mkdir(dir)

    return ret

def updateData(slugs):
    # Record auction data
    c = 1
    for slug in slugs:
        print 'Processing %s records (%d of %d)' % (slug, c, len(slugs))
        j = simplejson.load(urllib.urlopen(AUCTIONS_BASE % (slug)))

        t = int(time())
        def process(aucs, side):
            base = os.path.join(REALMS_DIR, slug, str(t))
            if not os.path.isdir(base):
                os.mkdir(base)
            f = open(os.path.join(base, side), 'w')
            f.write(simplejson.dumps(aucs, separators=(',',':')))
            f.close()
            print '\t%s: %d' % (side, len(aucs['auctions']))

        process(j['alliance'], 'a')
        process(j['horde'], 'h')
        process(j['neutral'], 'n')
        c+=1
    
    
def main():
   realms = updateRealms() 
   updateData(realms)

if __name__ == '__main__':
    main()
