import MySQLdb
import time
import datetime
from db_settings import DB_USER, DB_PASS
from money import Money

FIVE_HOURS = 18000000
ONE_DAY = 86400000

### Config

DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'wowzer'

conn = MySQLdb.connect(host = DB_HOST,
                        user = DB_USER,
                        passwd = DB_PASS,
                        db = DB_NAME)
cur = conn.cursor()


### Templates 

DB_CREATE = """
CREATE DATABASE IF NOT EXISTS wowzer
"""

# Table names are format countrycode_slug, eg. us-elune
DB_TABLE_META = """
CREATE TABLE IF NOT EXISTS %s_%s_meta(
    updated DATETIME
)
"""

DB_TABLE_AUCTIONS = """

CREATE TABLE IF NOT EXISTS %s_%s_%s_auctions(
    id INT NOT NULL AUTO_INCREMENT,
    PRIMARY KEY(id),

    auction INT,
    item INT,
    bid BIGINT,
    buyout BIGINT,
    quantity SMALLINT,
    owner VARCHAR(20),
    timeLeft SMALLINT,
    time DATETIME,

    INDEX(item),
    INDEX(time)
)

"""

DB_TABLE_REAGENTS = """
CREATE TABLE IF NOT EXISTS reagents (
    id INT NOT NULL AUTO_INCREMENT,
    PRIMARY KEY(id),

    item INT,
    reagent INT,

    INDEX(item),
    INDEX(reagent)
)
"""


### Write functions

TIMELEFT_MAPPING = {
    'VERY_LONG' : 0,
    'LONG' : 1,
    'MEDIUM' : 2,
    'SHORT' : 3,
}


def createReagentsTable():
    cur.execute(DB_TABLE_REAGENTS)
    conn.commit()
    print 'Table created'
    

def createRealmTables(newtables):
    for country, realm in newtables:
        cur.execute(DB_TABLE_META % (country, realm));
        cur.execute(DB_TABLE_AUCTIONS % (country, realm, 'a'));
        cur.execute(DB_TABLE_AUCTIONS % (country, realm, 'h'));
        cur.execute(DB_TABLE_AUCTIONS % (country, realm, 'n'));

    conn.commit();
    print 'Tables created'


def insertAuctions(info, aucs):
    country, realm, side = info
    now = datetime.datetime.now().isoformat();
    for auc in aucs:
        table = '%s_%s_%s_auctions' % (country, realm, side) 
        cur.execute("""
            INSERT INTO """+table+"""
            (auction, item, bid, buyout, quantity, owner, timeLeft, time)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)""",
                [auc['auc'], auc['item'], auc['bid'], auc['buyout'], 
                auc['quantity'], auc['owner'], 
                TIMELEFT_MAPPING[auc['timeLeft']],
                now])

    conn.commit();

### Query functions

class Row:
    def __init__(self, r):
        self.auc = int(r[0])
        self.item = int(r[1])
        self.bid = int(r[2])
        self.bidper = int(r[2])/int(r[4])
        self.buy = int(r[3])
        self.buyper = int(r[3])/int(r[4])
        self.quant = int(r[4])
        self.owner = r[5]
        self.timeLeft = int(r[6])
        self.time = r[7]

    def __str__(self):
        return 'auc #%d for item #%d x%d: (%s bid per) (%s buy per)' \
            % (self.auc, self.item, self.quant, Money(self.bidper), Money(self.buyper))

# General response
# Returns timestamp and dict containing keys bid, buy, each a tuple of low, high, avg
def spread(queryresults):
    results = [Row(x) for x in queryresults]

    # Find current min
    if len(results) < 1:
        return -1, {}

    ts_current = results[0].time
    high_bid = low_bid = results[0].bid
    high_buy = low_buy = results[0].buy
    total_bid = total_buy = 0
    c = 0
    for result in results:
        if result.time < ts_current:
            # No earlier items
            break

        if result.bid < low_bid:
            low_bid = result.bid
        if result.buy < low_buy:
            low_buy = result.buy
        if result.bid > high_bid:
            high_bid = result.bid
        if result.buy > high_buy:
            high_buy = result.buy

        total_bid += result.bid
        total_buy += result.buy
        c += 1

    avg_bid = float(total_bid) / c
    avg_buy = float(total_buy) / c
    return ts_current, {
        'bid': (low_bid, high_bid, avg_bid),
        'buy': (low_buy, high_buy, avg_buy),
    }


# Get items above a certain buy price
def getCurrentItems(rinfo, price_min, price_max):
    country, realm, side = rinfo
    table = '%s_%s_%s_auctions' % (country, realm, side)

    query = """
    SELECT time
    FROM """+table+"""
    ORDER BY time DESC LIMIT 1
    """
    cur.execute(query)
    
    x = cur.fetchall()
    if len(x) > 0:
        query = """
        SELECT auction,item,bid,buyout,quantity,owner,timeLeft,time
        FROM """+table+"""
        WHERE time = %s
        ORDER BY time DESC
        """
        queryargs = (x[0])
        cur.execute(query, queryargs)

        results = [Row(x) for x in cur.fetchall()]
        return [x for x in results 
            if x.buy >= price_min and x.buy <= price_max]        
    else:
        return None


# Hidden limit of five hours
def getCurrentSpread(rinfo, item):
    country, realm, side = rinfo
    table = '%s_%s_%s_auctions' % (country, realm, side)

    query = """
    SELECT auction,item,bid,buyout,quantity,owner,timeLeft,time
    FROM """+table+"""
    WHERE item=%s AND time >= FROM_UNIXTIME(%s)
    ORDER BY time DESC
    """
    queryargs = (item, int(time.time()-FIVE_HOURS))
    cur.execute(query, queryargs)

    return spread(cur.fetchall())

# Returns of status, avgBid, avgBO
# Days = days prior to now
def getDaysAvg(rinfo, item, days):
    country, realm, side = rinfo
    table = '%s_%s_%s_auctions' % (country, realm, side)

    query = """
    SELECT auction,item,bid,buyout,quantity,owner,timeLeft,time
    FROM """+table+"""
    WHERE item=%s AND time >= FROM_UNIXTIME(%s)
    ORDER BY time DESC
    """
    queryargs = (item, int(time.time()-(ONE_DAY*days)))
    cur.execute(query, queryargs)

    return spread(cur.fetchall())

# Returns x_axis (list of time); bid, buy (dicts of tuple (high, low, avg))
def series(queryresults):
    results = [Row(x) for x in queryresults]

    # Find current min
    if len(results) < 1:
        return None

    time = []
    bid = {'high':[],'low':[],'avg':[]}
    buy = {'high':[],'low':[],'avg':[]}

    ts_current = results[0].time
    high_bid = low_bid = results[0].bid
    high_buy = low_buy = results[0].buy
    total_bid = total_buy = 0
    c = 0

    for result in results:
        if result.time < ts_current:
            # new x axis
            time.append(ts_current)
            bid['high'].append(high_bid)
            buy['high'].append(high_buy)
            bid['low'].append(high_bid)
            buy['low'].append(high_buy)

            avg_bid = float(total_bid) / c
            avg_buy = float(total_buy) / c

            bid['avg'].append(avg_bid)
            buy['avg'].append(avg_buy)

            # reset
            ts_current = result.time
            high_bid = low_bid = result.bid
            high_buy = low_buy = result.buy
            total_bid = result.bid
            total_buy = result.buy
            c = 1
            continue

        # Continue computing series element
        if result.bid < low_bid:
            low_bid = result.bid
        if result.buy < low_buy:
            low_buy = result.buy
        if result.bid > high_bid:
            high_bid = result.bid
        if result.buy > high_buy:
            high_buy = result.buy

        total_bid += result.bid
        total_buy += result.buy
        c += 1
    
    return time, bid, buy

# Returns of status, avgTimeSeriesBid, avgTimeSeriesBuy
# Time series are lists
# Days = days prior to now
def getSeries(rinfo, item, days):
    country, realm, side = rinfo
    table = '%s_%s_%s_auctions' % (country, realm, side)

    query = """
    SELECT auction,item,bid,buyout,quantity,owner,timeLeft,time
    FROM """+table+"""
    WHERE item=%s AND time >= FROM_UNIXTIME(%s)
    ORDER BY time DESC
    """
    queryargs = (item, int(time.time()-(ONE_DAY*days)))
    cur.execute(query, queryargs)

    return series(cur.fetchall())

# Returns of status, avgBid, avgBO
def getEMA(realm, item, days):
    pass

# Returns reagents for item
def getReagents(item):
    query = """
    SELECT reagent
    FROM reagents
    WHERE item=%s
    """
    queryargs = (item)
    cur.execute(query, queryargs)

    return [x[0] for x in cur.fetchall()]

def saveReagents(item, ids):
    for id in ids:
        query = """
        INSERT INTO reagents (item, reagent)
        VALUES (%s, %s)
        """
        queryargs = (item, id)
        cur.execute(query, queryargs)
    conn.commit()
