# Item crafting arbitrage
# TODO arbitrage for entire supply chain (eg. mute gem, cut gem)

import urllib
from xml.etree.ElementTree import parse

import db

WOWHEAD_BASE = 'http://www.wowhead.com/item=%d&xml'

# Returns tuple: low BO for item, list of low BO for mats
def getCraftPricing(rinfo, item):
    # Look up mats for item number - check db first

    print 'Craft pricing', item

    print '\t Checking db'
    rs = db.getReagents(item)

    if len(rs) < 1:
        print '\t Grabbing from wowhead'

        # Not there, so check wowhead
        xml = parse(urllib.urlopen(WOWHEAD_BASE % (item)))
        ingreds = xml.findall('item/createdBy/spell/reagent')
        rs = [x.get('id') for x in ingreds]

        # Store in database
        print '\t Storing in db'
        db.saveReagents(item, rs)

    # ARBITRATE
    ts, prices = db.getCurrentSpread(rinfo, item)
    if ts == -1:
        return False

    crafted = prices['bid'][0]

    rprices = []
    for id in rs:
        ts, prices = db.getCurrentSpread(rinfo, id)
        if ts == None:
            return False
        rprices.append(prices['bid'][0])

    return crafted - sum(rprices), crafted, rprices

