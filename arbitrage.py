# Item crafting arbitrage
# TODO arbitrage for entire supply chain (eg. mute gem, then cut gem)

import urllib
from xml.etree.ElementTree import parse

import db
from money import Money

WOWHEAD_BASE = 'http://www.wowhead.com/item=%d&xml'

# Returns tuple: low BO for item, list of low BO for mats
def getCraftPricing(rinfo, item):
    # Look up mats for item number - check db first

    rs = db.getReagents(item)
    if len(rs) < 1:

        # Not there, so check wowhead
        xml = parse(urllib.urlopen(WOWHEAD_BASE % (item)))
        ingreds = xml.findall('item/createdBy/spell/reagent')
        rs = [x.get('id') for x in ingreds]

        # Store in database
        db.saveReagents(item, rs)

    # Compare prices, etc.
    ts, prices = db.getCurrentSpread(rinfo, item)
    if ts == -1 or 'buy' not in prices:
        return False

    crafted = prices['buy'][0]

    rprices = []
    for id in rs:
        ts, prices = db.getCurrentSpread(rinfo, id)
        if ts == None or 'buy' not in prices:
            return False
        rprices.append(prices['buy'][0])

    return crafted - sum(rprices), crafted, rprices

def findCraftable(rinfo, min_price=Money(gold=50), max_price=Money(gold=175)):
    items = db.getCurrentItems(rinfo, min_price, max_price)

    for item in items:
        print str(item), ':'
        makemoney, cid, craftprices = getCraftPricing(rinfo, item.item)
        if len(craftprices) > 0:
            craftprices = [str(Money(x)) for x in craftprices]
            print '\t(profit %s) (sell %s) (mats %s)' \
                % (str(Money(makemoney)), str(Money(cid)), craftprices)
