import MySQLdb
from db_settings import DB_USER, DB_PASS

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

# Table names are format countrycode-slug, eg. us-elune
DB_TABLE_META = """
CREATE TABLE IF NOT EXISTS %s_%s_meta(
    updated DATETIME
)
"""

DB_TABLE_AUCTIONS = """

CREATE TABLE IF NOT EXISTS %s_%s_auctions(
    id INT NOT NULL AUTO_INCREMENT,
    PRIMARY KEY(id),

    auction INT,
    item INT,
    bid INT,
    buyout INT,
    quantity INT,
    owner VARCHAR(30),
    timeLeft INT,
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
        cur.execute(DB_TABLE_AUCTIONS % (country, realm));
        cur.execute(DB_TABLE_META % (country, realm));

    conn.commit();


def insertAuctions(aucs, info):
    country, realm = info
    for auc in aucs:
        cur.execute("""
            INSERT INTO %s_%s (auction, item, bid, buyout, quantity, owner, timeLeft, time)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, NOW())
        """, [auc['auction'], auc['item'], auc['bid'], auc['buyout'], 
                auc['quantity'], auc['owner'], 
                TIMELEFT_MAPPING[auc['timeLeft']]])

    conn.commit();

### Query functions
# http://www.tutorialspoint.com/python/python_database_access.htm

# Returns tuple of status, lowbid, lowBO
def getCurrentLow(realm, item):
    pass

# Returns of status, avgBid, avgBO
# Days = days prior to now
def getDaysAvg(realm, item, days):
    pass

# Returns of status, avgTimeSeriesBid, avgTimeSeriesBuy
# Time series are lists
# Days = days prior to now
def getSeries(realm, item, days):
    pass

# Returns of status, avgBid, avgBO
def getEMA(realm, item, days):
    pass

