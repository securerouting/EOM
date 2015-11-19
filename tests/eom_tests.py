""" A test suite for eom. 

Nothing to see here currently.
"""
import sys
import os
import unittest
import netaddr
from pprint import pprint
from StringIO import StringIO
from eom.analyzer import EOMAnalyzerEngine
from eom.aggregator import EOMAggregator
from eom.reporter import EOMReporter
from eom.generic_poller import EOMGenericPoller
from rpki.rtr.channels import Timestamp

TEST_DB = "/tmp/eom_test_db.sqlite"

class RPKITestCase:
    def __init__(self, sql):
        self.sql = sql
        self.cache_ids = []
        self.rtr_ids = []
        self.vrps = []
        self.rib_items = []

    def add_vrp(self, cache_id, asn, prefix, prefixlen, maxlen):
        ipstr = unicode(str(prefix) + "/" + str(prefixlen), "utf-8")
        prefix_min = EOMGenericPoller.get_ip_str(netaddr.IPNetwork(ipstr).first)
        prefix_max = EOMGenericPoller.get_ip_str(netaddr.IPNetwork(ipstr).last)
        if cache_id not in self.cache_ids:
            self.cache_ids.append(cache_id)
        # cache_id|asn|prefix|prefixlen|max_prefixlen|prefix_min|prefix_max
        self.vrps.append((cache_id, asn, prefix, prefixlen, maxlen, prefix_min, prefix_max))
       
    def add_rib_entry(self, rtr_id, idx, prefix, prefixlen, patharr, 
                      nexthop, metric=0, locpref=0, weight=0):
        ipstr = unicode(str(prefix) + "/" + str(prefixlen), "utf-8")
        prefix_min = EOMGenericPoller.get_ip_str(netaddr.IPNetwork(ipstr).first)
        prefix_max = EOMGenericPoller.get_ip_str(netaddr.IPNetwork(ipstr).last)
        pathbutone = patharr 
        orig_asn = int(pathbutone.pop())
        pathbutonestr = ' '.join(str(x) for x in patharr)
        if rtr_id not in self.rtr_ids:
            self.rtr_ids.append(rtr_id)
        # rtr_id|idx|status|pfx|pfxlen|pfxstr_min|pfxstr_max|nexthop|metric|locpref|weight|pathbutone|orig_asn|route_orig
        self.rib_items.append((rtr_id, idx, '*>i', prefix, prefixlen,
                prefix_min, prefix_max, nexthop, metric, locpref, weight,
                pathbutonestr, orig_asn, 'i')) 
         
    def stage(self):
        cur = self.sql.cursor()
        now = Timestamp.now()

        # Clear state
        cur.execute("DELETE FROM cache")
        cur.execute("DELETE FROM prefix")
        cur.execute("DELETE FROM routerkey")
        cur.execute("DELETE FROM rtr_cache")
        cur.execute("DELETE FROM rtr_rib")

        # Update cache ids
        for cid in self.cache_ids:
            # cache_id|host|port|version|nonce|serial|updated|refresh|retry|expire
            cur.execute("INSERT INTO cache (cache_id, host, port, \
                            version, nonce, serial, updated, refresh, \
                            retry, expire) VALUES (?,?,?,?,?,?,?,?,?,?)", \
                        (cid, 'localhost', 1234, 0, 12345, 1000, now, 3600, 600, 7200))

        # Update router ids
        for did in self.rtr_ids:
            # rtr_id|device
            cur.execute("INSERT INTO rtr_cache (device) VALUES (?)", (did,))
            
        # Update all VRPs
        for v in self.vrps:
            # cache_id|asn|prefix|prefixlen|max_prefixlen|prefix_min|prefix_max
            cur.execute("INSERT INTO prefix (cache_id, asn, prefix, \
                            prefixlen, max_prefixlen, prefix_min, prefix_max) \
                         VALUES (?,?,?,?,?,?,?)", v)

        # Update all RIB entries
        for r in self.rib_items:
            # rtr_id|idx|status|pfx|pfxlen|pfxstr_min|pfxstr_max|nexthop|metric|locpref|weight|pathbutone|orig_asn|route_orig
            cur.execute("INSERT INTO rtr_rib (rtr_id, idx, status, \
                            pfx, pfxlen, pfxstr_min, pfxstr_max, \
                            nexthop, metric, locpref, weight, \
                            pathbutone, orig_asn, route_orig) \
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", r)
        self.sql.commit()
        


class MapResourceTests(unittest.TestCase):
    """The main test driver."""

    def setUp(self):
        self.a = EOMAggregator(dbfile=TEST_DB)
        self.sql = self.a.get_sql_connection()

    def tearDown(self):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass

    def runTest(self):
        pass

    def test_db(self):
        self.assertTrue(self.sql)

    def test_good_roa(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 42, '10.0.0.0', 16, 16)
        t.add_rib_entry(1, 1, '10.0.0.0', 16, [1, 2, 42], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        self.assertFalse(badroutes) 

    def test_good_range(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 42, '10.0.0.0', 12, 16)
        t.add_rib_entry(1, 1, '10.0.0.0', 16, [1, 2, 42], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        self.assertFalse(badroutes) 

    def test_good_unknown(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 42, '10.0.0.0', 18, 20)
        t.add_rib_entry(1, 1, '10.0.0.0', 16, [1, 2, 42], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        self.assertFalse(badroutes) 

    def test_bad_origin(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 42, '10.0.0.0', 16, 24)
        t.add_rib_entry(1, 1, '10.0.0.0', 16, [1, 2, 666], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        EOMReporter().show(badroutes)
        self.assertTrue(badroutes) 

    def test_bad_too_long(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 42, '10.0.0.0', 8, 12)
        t.add_rib_entry(1, 1, '10.0.0.0', 16, [1, 2, 42], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        EOMReporter().show(badroutes)
        self.assertTrue(badroutes) 

    def test_multiple_match1(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 6, '10.0.0.0', 16, 24)
        t.add_vrp(1, 42, '10.0.0.0', 16, 20)
        t.add_rib_entry(1, 1, '10.0.0.0', 24, [1, 2, 6], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        self.assertFalse(badroutes) 

    def test_multiple_match2(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 6, '10.0.0.0', 16, 24)
        t.add_vrp(1, 42, '10.0.0.0', 16, 20)
        t.add_rib_entry(1, 1, '10.0.0.0', 16, [1, 2, 42], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        self.assertFalse(badroutes) 

    def test_multiple_mismatch_asn(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 6, '10.0.0.0', 16, 24)
        t.add_vrp(1, 42, '10.0.0.0', 16, 20)
        t.add_rib_entry(1, 1, '10.0.0.0', 22, [1, 2, 42], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        EOMReporter().show(badroutes)
        self.assertTrue(badroutes) 

    def test_multiple_mismatch_len(self):
        t = RPKITestCase(self.sql)
        analyzer = EOMAnalyzerEngine(self.a)
        t.add_vrp(1, 6, '10.0.0.0', 16, 24)
        t.add_vrp(1, 42, '10.0.0.0', 16, 20)
        t.add_rib_entry(1, 1, '10.0.0.0', 26, [1, 2, 6], '192.168.1.1')
        t.stage()
        badroutes = analyzer.analyze()
        EOMReporter().show(badroutes)
        self.assertTrue(badroutes) 


if __name__ == '__main__':
    unittest.main()
