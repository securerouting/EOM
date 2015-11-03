"""Implementation of the router configuration fetcher for EOM.

This module interfaces with routers in order to fetch routing related
information. The received data is saved through the aggregator module to
an internal data store.

For parsing approach, see:
http://stackoverflow.com/questions/30997205/pyparsing-parsing-ciscos-show-ip-bgp
"""

import subprocess
import json
import re
from rpki.rtr.channels import Timestamp
from eom.generic_poller import EOMGenericPoller
from pprint import pprint
import netaddr
import pipes
from pyparsing import col,Word,Optional,alphas,nums,\
                      ParseException,Combine,oneOf,Literal,\
                      Group,OneOrMore,ZeroOrMore,hexnums,Or

class RtrRIBState:
    """A class that interfaces between router output data and the database"""
    def __init__(self, sql, device):
        """Constructor.

        Args:
            sql: A handle to the sql database
            device: the device identifier
        """
        self.updated = 0
        self.device = pipes.quote(device) 
        self.sql = sql
        self.rib_row = self.define_grammar()

    #Format of sh ip bgp output:
    #
    #BGP table version is 0, local router ID is 192.168.56.101
    #Status codes: s suppressed, d damped, h history, * valid, > best, i -
    #internal,
    #              r RIB-failure, S Stale, R Removed
    #Origin codes: i - IGP, e - EGP, ? - incomplete
    #
    #   Network          Next Hop            Metric LocPrf Weight Path
    #*>i1.9.0.0/16       192.168.56.1            10      0      0 3257 4788 i
    #*>i1.9.21.0/24      192.168.56.1                    0      0 7018 6453 4788 4788 i
    #
    #Total number of prefixes 2
    #
    def define_grammar(self):
        """Define the grammar for the BGP output.
    
        See also:
        http://stackoverflow.com/questions/30997205/pyparsing-parsing-ciscos-show-ip-bgp
        """
        ip4Field = Word(nums, max=3)
        ip4Addr = Combine(ip4Field + "." + ip4Field + "." + ip4Field + "." + ip4Field)
        hexint = Word(hexnums,exact=2)
        ip6Field = Or([hexint, Literal(":")])
        ip6Addr = Combine(OneOrMore(ip6Field))
        ipAddr = Or([ip4Addr, ip6Addr])
        status_code = Combine(Optional(oneOf("s d h * r")) + Optional(Literal(">")) + Optional(Literal("i")))
        next_hop = ipAddr
        integer = Word(nums).setParseAction(lambda t: int(t[0])).setName("integer")
        metric = Optional(self._tableValue(integer, 41, 46))
        locpref = Optional(self._tableValue(integer, 48, 53))
        weight = Optional(self._tableValue(integer, 55, 60))
        path = Group(OneOrMore(Word(nums)))
        origin = oneOf("i e ?")

        return status_code("status") + ipAddr("pfx") + Literal("/") + \
            Word(nums,max=2)("pfxlen") + ipAddr("nexthop") + \
            metric("metric") + locpref("locpref") + weight("weight") + \
            path("path") + origin("route_orig")

    def _mustMatchCols(self, startloc,endloc):
        """specify constraint for particular field in output.
    
        See also:
        http://stackoverflow.com/questions/30997205/pyparsing-parsing-ciscos-show-ip-bgp
        """
        def pa(s,l,t):
            if not startloc <= col(l,s) <= endloc:
                raise ParseException(s,l,"text not in expected columns")
        return pa

    def _tableValue(self, expr, colstart, colend):
        """helper to define values in a space-delimited table
    
        See also:
        http://stackoverflow.com/questions/30997205/pyparsing-parsing-ciscos-show-ip-bgp
        """
        return expr.copy().addParseAction(self._mustMatchCols(colstart,colend))

    def parse(self, output):
        """Parse the router RIB dump
    
        Args:
            output: The output generated by do_poll.py

        Returns:
            A dict containing parsed RIB entries
        """
        results = []
        if output:
            j = json.loads(output)
            if self.device not in j:
                return results
            ribdump = j[self.device]["show ip bgp"]
            for l in ribdump.split("\r\n"):
                try:
                    r = self.rib_row.parseString(l)
                    results.append(r)
                except ParseException:
                    # Ignore lines we cannot parse
                    pass
        return results

    def get_ip_str(self, ipint):
        """Convert an IP int to an ordinal IP string.

        Convert the IP int first to its dotted or string form. Then
        expand each component so that determining ranges between two of
        these strings becomes possible.

        Args:
            ipint: int value of an IP address

        Returns:
            Expanded string representation.
        """
        ipaddr = None
        ipobj = netaddr.IPAddress(ipint)
        if ipobj.version == 6:
            ipaddr = ipobj.format(netaddr.ipv6_verbose)
            ipaddr = ipaddr.upper()
        else:
            dotted = str(ipobj).split(".")
            ipaddr = '.'.join([ str(i).zfill(3) for i in dotted ])
        return ipaddr

    def store_in_db(self, rib):
        """Store the given RIB data into the database.

        Updating the database involves two steps. First is to make sure
        that old entries are deleted and then to add each RIB entry into
        its own row indexed by the router id.

        Args:
            rib: A dict containing parsed RIB information

        Returns:
            None
        """
        if rib:
            print "Updating Database with new data."
            #pprint(rib)
            cur = self.sql.cursor()
            cur.execute("SELECT rtr_id, device FROM rtr_cache WHERE device = ?", (self.device, ))
            try:
                rtr_id, device = cur.fetchone()
                cur.execute("DELETE FROM rtr_cache WHERE device = ?", (self.device, ))
                raise TypeError # Simulate lookup failure case
            except TypeError:
                cur.execute("INSERT INTO rtr_cache (device) VALUES (?)", (self.device,))
                rtr_id = cur.lastrowid
            # Update RIB info
            idx = 0
            for r in rib:
                # Split path into pathbutone and orig_asn
                pathbutone = r.path
                orig_asn = pathbutone.pop()
                pathbutonestr = ' '.join(pathbutone)
                ipstr = unicode(str(r.pfx) + "/" + str(r.pfxlen), "utf-8")
                prefixint_min = netaddr.IPNetwork(ipstr).first
                prefixint_max = netaddr.IPNetwork(ipstr).last
                values = (rtr_id, 
                          idx,
                          r.status, 
                          r.pfx, 
                          int(r.pfxlen), 
                          self.get_ip_str(prefixint_min),
                          self.get_ip_str(prefixint_max),
                          r.nexthop, 
                          int(r.metric) if r.metric else 0, 
                          int(r.locpref) if r.locpref else 0, 
                          int(r.weight) if r.weight else 0, 
                          pathbutonestr, 
                          int(orig_asn), 
                          r.route_orig)
                cur.execute("INSERT INTO rtr_rib (rtr_id, idx, status, "
                            "pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop, "
                            "metric, locpref, weight, pathbutone, orig_asn, route_orig) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            values)
                idx += 1
            self.sql.commit()

    def update(self, output):
        """Parse output and store results to database.

        Args:
            output: The output generated by do_poll.py

        Returns:
            A dict containing parsed RIB entries
        """
        ribinfo = self.parse(output)
        if ribinfo:
            self.store_in_db(ribinfo)


class EOMRtrRIBFetcher(EOMGenericPoller):
    """Poller for fetching RIB information from a router instance."""
    def __init__(self, args, aggregator):
        """Instantiate the router status fetcher object.

        Args:
            device(Str): Device identifier
            aggregator(EOMAggregator): The data aggregator object
        """
        assert aggregator != None
        self.device = pipes.quote(args.device)
        if args.reset_session:
            aggregator.reset_rtr_rib_session(self.device)
        self.sql = aggregator.get_sql_connection()
        self.poll_interval = args.poll_interval
        self.ribstate = RtrRIBState(self.sql, self.device)
        self.last_update = self.ribstate.updated

    def cleanup(self):
        pass

    def poll(self, now):
        """Fetch data from configured routers.

        Process the fetch queue to identfy fetch events that must be
        processed during this time interval. Store all data received
        to the internal data store through the aggregator module.

        The data is fetched using the do_poll.py script run as a
        sub-process. This is not optimal, but we are constrained by the
        fact that the Trigger module, which pulls data from the router
        and the rpki-rtr implementation which pulls data from a rpki-rtr
        manager instance use different event loops. In the future, it
        would probably make sense to modify the rpki-rtr implementation
        to use the Python twisted framework.

        Args:
            now: current timestamp

        Returns:
            (Boolean, int): A tuple comprising of a pending status and
                            the timestamp for the next event in the queue.
        """
        if now - self.last_update > self.poll_interval:
            # Start a fresh lookup
            output = subprocess.check_output(["python", "-W ignore", "do_poll.py", "--device", self.device])
            #output = subprocess.check_output(["clogin", "-c 'show ip bgp'", self.device])
            #output = str('{"quagga.vm": {"show ip bgp": "BGP table version is 0, local router ID is 192.168.56.101\\r\\nStatus codes: s suppressed, d damped, h history, * valid, > best, i - internal,\\r\\n              r RIB-failure, S Stale, R Removed\\r\\nOrigin codes: i - IGP, e - EGP, ? - incomplete\\r\\n\\r\\n   Network          Next Hop            Metric LocPrf Weight Path\\r\\n*>i1.9.0.0/16       192.168.56.1            10      0      0 3257 4788 i\\r\\n*>i1.9.21.0/24      192.168.56.1                    0      0 7018 6453 4788 4788 i\\r\\n\\r\\nTotal number of prefixes 2\\r\\n"}}')
            self.ribstate.update(output)
            self.last_update = Timestamp.now()

        # Since we're doing the lookup as a sub-process we're never
        # waiting for data. So the pending status is always false.
        return (False, self.last_update + self.poll_interval)


