# Item crafting arbitrage
# TODO arbitrage for entire supply chain (eg. mute gem, then cut gem)

import urllib
from xml.etree.ElementTree import parse

import db
from money import Money

WOWHEAD_BASE = 'http://www.wowhead.com/item=%d&xml'

# Returns tuple: low BO for item, list of low BO for mats
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
    for id in reagents:
        ts, prices = spreads[id]
        if ts == None or 'buy' not in prices:
            return False
        rprices.append(prices['buy'][0])

    return crafted - sum(rprices), crafted, rprices

def findCraftable(rinfo, min_price=Money(gold=50), max_price=Money(gold=175)):
    items = db.getCurrentItems(rinfo, min_price, max_price)

    lookedup  = {}
    for item in items:
        if item in lookedup:
            continue
        lookedup[item] = True

        pricingreturn = getCraftPricing(rinfo, item.item)
        if pricingreturn:
            makemoney, cid, craftprices = pricingreturn
            # Print profitable items
            if len(craftprices) > 0 and makemoney > 0:
                craftprices = [str(Money(x)) for x in craftprices]
                print '(profit %s) (sell %s) (mats %s)' \
                    % (str(Money(makemoney)), str(Money(cid)), craftprices)
