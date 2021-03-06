"""Implementation of the data aggregation module for EOM.

This module interfaces with various fetcher modules and stores the
retrieved data into a persistent data store (database).
"""

import sqlite3
import os
import json
import hashlib

class EOMAggregator:
    """A RPKI-Rtr and RIB data aggregator."""

    def __init__(self, dbfile="eom_default_db.sqlite", init_db=False):
        """Instantiate the data aggregator object.

        Args:
            dbfile (str): The name of the database file. If a value is
                          not provided, it defaults to
                          'eom_default_db.sqlite'
        """
        self.sql = None
        missing = not os.path.exists(dbfile)
        self.sql = sqlite3.connect(dbfile, detect_types = sqlite3.PARSE_DECLTYPES)
        self.sql.text_factory = str
        if missing or init_db:
            self.init_rpki_rtr_tables()
            self.init_rib_tables()
            self.init_analysis_tables()

    def get_sql_connection(self):
        """ Get an instance to the sql connection object.

        Args:
            None
        """
        return self.sql

    def init_rpki_rtr_tables(self):
        """Initialize rpki-rtr database tables.
       
        Three tables are created - one that keeps track of the rpki-rtr
        session, one that keeps track of the prefixes associated with
        each active rpki-rtr session, and finally one for storing router
        key information.

        Args:
            None
        """
        cur = self.sql.cursor()
        cur.execute("PRAGMA foreign_keys = on")
        cur.execute('''
                CREATE TABLE cache (
                    cache_id        INTEGER PRIMARY KEY NOT NULL,
                    host            TEXT NOT NULL,
                    port            TEXT NOT NULL,
                    version         INTEGER,
                    nonce           INTEGER,
                    serial          INTEGER,
                    updated         INTEGER,
                    refresh         INTEGER,
                    retry           INTEGER,
                    expire          INTEGER,
                    UNIQUE          (host, port))''')
        cur.execute('''
                CREATE TABLE prefix (
                    prefix_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_id        INTEGER NOT NULL
                                    REFERENCES cache(cache_id)
                                    ON DELETE CASCADE
                                    ON UPDATE CASCADE,
                    asn             INTEGER NOT NULL,
                    prefix          TEXT NOT NULL,
                    prefixlen       INTEGER NOT NULL,
                    max_prefixlen   INTEGER NOT NULL,
                    prefix_min      TEXT,
                    prefix_max      TEXT,
                    UNIQUE          (cache_id, asn, prefix, prefixlen, max_prefixlen))''')
        cur.execute('''
                CREATE TABLE routerkey (
                    cache_id        INTEGER NOT NULL
                                    REFERENCES cache(cache_id)
                                    ON DELETE CASCADE
                                    ON UPDATE CASCADE,
                    asn             INTEGER NOT NULL,
                    ski             TEXT NOT NULL,
                    key             TEXT NOT NULL,
                    UNIQUE          (cache_id, asn, ski),
                    UNIQUE          (cache_id, asn, key))''')
        self.sql.commit()

    def init_rib_tables(self):
        """Initialize RIB database tables.
       
        Two tables are created. One stores the rtr ID associated with a
        given device that is to be queried, while the second stores
        different route attributes gleaned from 'sh ip bgp' command.

        Args:
            None
        """
        cur = self.sql.cursor()
        cur.execute("PRAGMA foreign_keys = on")
        cur.execute('''
                CREATE TABLE rtr_cache (
                    rtr_id          INTEGER PRIMARY KEY NOT NULL,
                    device          TEXT NOT NULL,
                    rtrupdt         INTEGER,
                    UNIQUE          (device))''')
        cur.execute('''
                CREATE TABLE rtr_rib (
                    rtr_id          INTEGER NOT NULL
                                    REFERENCES rtr_cache(rtr_id)
                                    ON DELETE CASCADE
                                    ON UPDATE CASCADE,
                    idx             INTEGER NOT NULL,
                    status          TEXT,
                    pfx             TEXT NOT NULL,
                    pfxlen          INTEGER NOT NULL,
                    pfxstr_min      TEXT NOT NULL,
                    pfxstr_max      TEXT NOT NULL,
                    nexthop         TEXT NOT NULL,
                    metric          INTEGER,
                    locpref         INTEGER,
                    weight          INTEGER,
                    pathbutone      TEXT,
                    orig_asn        INTEGER NOT NULL,
                    route_orig      TEXT)''')
        self.sql.commit()

    def init_analysis_tables(self):
        """Initialize RIB database tables.
       
        Two tables are created. One stores the report ID associated with a
        given run, while the second stores the contents of the report
        indexed by the report id.

        Args:
            None
        """
        cur = self.sql.cursor()
        cur.execute("PRAGMA foreign_keys = on")
        cur.execute('''
                CREATE TABLE report_index (
                    report_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_hash     TEXT NOT NULL,
                    device          TEXT NOT NULL,
                    timestamp       INTEGER NOT NULL)''')
        cur.execute('''
                CREATE TABLE report_detail (
                    route_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_hash     TEXT NOT NULL,
                    invalid         TEXT NOT NULL,
                    status          TEXT NOT NULL,
                    pfx             TEXT NOT NULL,
                    pfxlen          TEXT NOT NULL,
                    pfxstr_min      TEXT NOT NULL,
                    pfxstr_max      TEXT NOT NULL,
                    nexthop         TEXT NOT NULL,
                    metric          TEXT NOT NULL,
                    locpref         TEXT NOT NULL,
                    weight          TEXT NOT NULL,
                    pathbutone      TEXT NOT NULL,
                    orig_asn        TEXT NOT NULL,
                    route_orig      TEXT NOT NULL)''')
        cur.execute('''
                CREATE TABLE fconstraints (
                    fcons_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id        TEXT NOT NULL
                                    REFERENCES report_detail(route_id),
                    host            TEXT NOT NULL,
                    port            TEXT NOT NULL,
                    asn             TEXT NOT NULL,
                    prefix          TEXT NOT NULL,
                    prefixlen       INTEGER NOT NULL,
                    max_prefixlen   INTEGER NOT NULL)''')
        self.sql.commit()

    def reset_rpki_rtr_session(self, host, port):
        """Reset an existing rpki-rtr session.

        Reset any existing rpki-rtr session for the given host and
        port.

        Arguments:
            host (string): the rpki-rtr server host 
            port (string): the rpki-rtr server port 
        """
        cur = self.sql.cursor()
        cur.execute("PRAGMA foreign_keys = on")
        cur.execute("DELETE FROM cache WHERE host = ? and port = ?", (host, port))
        self.sql.commit()

    def reset_rtr_rib_session(self, device):
        """Reset a RIB query session.

        Delete any state corresponding to a RIB query that was issued
        for a particular router device.

        Arguments:
            device(string): The device identifier.

        """
        cur = self.sql.cursor()
        cur.execute("PRAGMA foreign_keys = on")
        cur.execute("DELETE FROM rtr_cache WHERE device = ?", (device, ))
        self.sql.commit()

    def get_rpki_rib(self):
        """Fetch rib information in conjunction with rpki information.

        Construct a database 'join' of the contents of currently available
        rpki-rtr information with currently available RIB information.
        The join is constructed over matching prefix ranges; that is,
        for cases where the rpki rtr ROA covers the route prefix in the
        RIB.

        Arguments:
            None
        """
        cur = self.sql.cursor()
        cur.execute("SELECT DISTINCT host, port, device, idx, asn, prefix, prefixlen, "
                    "   max_prefixlen, status, pfx, pfxlen, pfxstr_min, pfxstr_max, "
                    "   nexthop, metric, locpref, weight, pathbutone, orig_asn, route_orig "
                    "FROM prefix "
                    "   INNER JOIN rtr_rib ON prefix_min <= pfxstr_min AND pfxstr_max <= prefix_max"
                    "   INNER JOIN rtr_cache ON rtr_cache.rtr_id = rtr_rib.rtr_id"
                    "   INNER JOIN cache ON cache.cache_id = prefix.cache_id", ())
        return cur.fetchall()

    def get_covering(self, device, pfxstr_min, pfxstr_max):
        """Fetch route entries that cover a given prefix range.

        Select those routes whose advertised address range covers the
        given prefix range.

        Arguments:
            device(string): the device name
            pfxstr_min(string): the lower value in the prefix range
            pfxstr_max(string): the upper value in the prefix range
        """
        cur = self.sql.cursor()
        cur.execute("SELECT idx, status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop, metric, "
                    "   locpref, weight, pathbutone, orig_asn, route_orig "
                    "FROM rtr_rib "
                    "INNER JOIN rtr_cache ON rtr_cache.rtr_id = rtr_rib.rtr_id "
                    "WHERE device = ? AND pfxstr_min <= ? AND pfxstr_max >= ?",
                    (device, pfxstr_min, pfxstr_max))
        return cur.fetchall()


    def get_report_hash(self, consolidated):
        """Get a hash value that corresponds to the consolidated routes
           
        The consolidated routes are structured as a dict. The keys in
        the dict are the index values of the routes. The values against
        each key is a tuple with three values

        Arguments:
            val1: valid invalid unknown status ('V'/'I'/'-')
            val2: RIB tuple with the following fields 
            (status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop, 
            metric, locpref, weight, pathbutone, orig_asn, route_orig)
            val3: A list of tuples that reflect ROA constraints
            [(asn, prefix, prefixlen, max_prefixlen)...]
        """
        jsonstr = json.dumps(consolidated, sort_keys=True)
        hashobj = hashlib.sha1(jsonstr)
        hexval = hashobj.hexdigest()
        return hexval 

    def store_analysis_results(self, data, ts):
        """Store the result into the database"""
        cur = self.sql.cursor()
        for rtr in data:
            report_hash = self.get_report_hash(data[rtr])
            cur.execute("INSERT INTO report_index (report_hash, device, timestamp) VALUES (?, ?, ?)", (report_hash, rtr, ts))
            report_id = cur.lastrowid
            # Check if the report_hash already exists 
            # if not, then add the route entries
            cur.execute("SELECT route_id FROM report_detail WHERE report_hash = ?", (report_hash,))
            rdata = cur.fetchone()
            if rdata is None:
                for (i, v) in sorted(data[rtr].items(), key=lambda x:int(x[0])):
                    args = [report_hash]
                    args.append(v[0])
                    args.extend(v[1])
                    cur.execute("INSERT INTO report_detail (report_hash, invalid, status, pfx, pfxlen, "
                                "pfxstr_min, pfxstr_max, nexthop, metric, locpref, weight, "
                                "pathbutone, orig_asn, route_orig) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                                (args))
                    route_id = cur.lastrowid
                    if v[2]:
                        # should be a list of tuples of constraints that failed
                        for (host, port, asn, prefix, prefixlen, max_prefixlen) in v[2]:
                            cur.execute("INSERT INTO fconstraints (route_id, host, port, asn, prefix, prefixlen, max_prefixlen) "
                                        "VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                        (route_id, host, port, asn, prefix, prefixlen, max_prefixlen))
        self.sql.commit()
