# Item crafting arbitrage
# TODO arbitrage for entire supply chain (eg. mute gem, then cut gem)

import urllib
import time
from xml.etree.ElementTree import parse

import db
from money import Money

WOWHEAD_BASE = 'http://www.wowhead.com/item=%d&xml'

# Returns tuple of profit and pricing information
def getCraftPricing(rinfo, item):
    wowheadxml = None

    # Look up mats for item number - check db first
    reagents = db.getReagents(item)
    if len(reagents) < 1:
        # Not there, so check wowhead
        wowheadxml = parse(urllib.urlopen(WOWHEAD_BASE % (item)))
        ingreds = wowheadxml.findall('item/createdBy/spell/reagent')
        reagents = [x.get('id') for x in ingreds]
        item_map = [(x.get('id'), x.get('name')) for x in ingreds]

        # Store in databases
        db.saveReagents(item, reagents)
        db.saveItems(item_map)

    # Grab item name
    item_name = db.getItemName(item)
    if not item_name:
        # Look it up
        if not wowheadxml:
            wowheadxml = parse(urllib.urlopen(WOWHEAD_BASE % (item)))
        item_name = wowheadxml.find('item/name').text
        db.saveItems([(item, item_name)])


    # Compare prices, etc.
    
    # Query spreads for item and its reagents
    spreads = db.getMultiCurrentSpread(rinfo, [item] + reagents)

    ts, prices = spreads[item]
    if ts == -1 or 'buy' not in prices:
        return False

    crafted = prices['buy'][0]

    rprices = []
    rnames = []
    for id in reagents:
        rnames.append(db.getItemName(id))
        ts, prices = spreads[id]
        if ts == None or 'buy' not in prices:
            return False
        rprices.append(prices['buy'][0])

    return {
        'item': item_name,
        'reagents': rnames,

        'profit': crafted - sum(rprices),
        'sell': crafted,
        'buy': rprices,
    }

def findCraftable(rinfo, min_price=Money(gold=50), max_price=Money(gold=150)):
    print 'Doing arbitrage calcs...'
    items = db.getCurrentItems(rinfo, min_price.val(), max_price.val())

    lookedup  = {}
    ret = []
    for item in items:
        if item.item in lookedup:
            continue
        lookedup[item.item] = True

        pricing = getCraftPricing(rinfo, item.item)
        if pricing:
            # Print profitable items
            if len(pricing['buy']) > 0 and pricing['profit'] > 0:
                print 'Producing timeseries for', item.item
                # Convert datetimes to unix timestamps
                series = db.getSeries(rinfo, item.item, 2)
                series['time'] = [time.mktime(x.timetuple()) for x in series['time']]
                # Not interested in these things yet
                del series['bid']
                #del series['buy']
                pricing['series'] = series
                ret.append(pricing)
    return ret
