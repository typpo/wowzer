import MySQLdb
import time
import datetime
from db_settings import DB_USER, DB_PASS

FIVE_HOURS = 18000000
ONEONE__DAY = 86400000

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


### Write functions

TIMELEFT_MAPPING = {
    'VERY_LONG' : 0,
    'LONG' : 1,
    'MEDIUM' : 2,
    'SHORT' : 3,
}


def createTables(newtables):
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
# http://www.tutorialspoint.com/python/python_database_access.htm

class Row:
    def __init__(self, r):
        self.auc = r[0]
        self.item = r[1]
        self.bid = r[2]
        self.buy = r[3]
        self.quant = r[4]
        self.owner = r[5]
        self.timeLeft = r[6]
        self.time = r[7]

# General response
# Returns timestamp and dict containing keys bid, buy, each a tuple of low, high, avg
def spread(queryresults)
    results = [Row(x) for x in queryresults]

    # Find current min
    if len(results) < 1:
        return None

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
def getSeries(realm, item, days):
    pass

# Returns of status, avgBid, avgBO
def getEMA(realm, item, days):
    pass

