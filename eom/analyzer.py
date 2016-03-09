"""Implementation of the analyzer module for EOM.

This module controls most of the EOM tool's operation. It accepts
preferences from the user, translates that data to configuration
parameters for the various modules, uses an internal scheduler to invoke
the fetch routines for various fetcher modules, extracts pertinent
streams of data from the aggregator module and other data stores, and
feeds such data to data analysis modules for further processing and
report generation. 
"""

import asyncore
import argparse
import sys
import time

from rpki.rtr.channels import Timestamp
from rpki.rtr.client import PDU
from eom.rpki_rtr_cli import EOMRPKIRtrCli
from eom.rtr_poller import EOMRtrRIBFetcher
from eom.aggregator import EOMAggregator
from eom.reporter import EOMReporter
from collections import defaultdict, OrderedDict
from pprint import pprint

class EOMAnalyzer:
    def __init__(self, aggregator):
        self.aggregator = aggregator
        pass

    def analyze(self):
        """Extract data from database and analyze.

        Get the list of RIB entries and associated RPKI information to
        be analyzed from the aggregator. Identify valid, invalid and
        unknown prefixes and finally display the output through the 
        EOMReporter module.

        Args:
            None

        Returns:
            A result dict structure
        """
        rib_good_info = defaultdict(dict)
        rib_bad_info = defaultdict(dict)
        mismatch = defaultdict(dict)

        toprocess = self.aggregator.get_rpki_rib()
        for (rtr_id, index, asn, prefix, prefixlen, max_prefixlen, 
                status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop,
                metric, locpref, weight, pathbutone, orig_asn,
                route_orig) in toprocess:
            
            # Create a RIB entry tuple
            rib_tup = (status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop,
                       metric, locpref, weight, pathbutone, orig_asn, route_orig)

            # The RPKI prefix must contain the advertised prefix
            if pfxlen < prefixlen:
                continue

            if index in rib_good_info[rtr_id]:
                continue

            if asn == orig_asn and pfxlen <= max_prefixlen:
                if index in rib_bad_info[rtr_id]:
                    del rib_bad_info[rtr_id][index]
                if index in mismatch[rtr_id]:
                    del mismatch[rtr_id][index]
                rib_good_info[rtr_id][index] = rib_tup
            else:
                rib_bad_info[rtr_id][index] = (pfxstr_min, pfxstr_max, rib_tup)
                rpkirtrpfxstr = prefix + "/" + "[" + str(prefixlen) + '-' + str(max_prefixlen) + "]"
                if index in mismatch[rtr_id]:
                    mismatch[rtr_id][index].append((asn, rpkirtrpfxstr))
                    mismatch[rtr_id][index] = list(set(mismatch[rtr_id][index]))
                else:
                    mismatch[rtr_id][index] = [(asn, rpkirtrpfxstr)]

        # return all affected paths
        consolidated = defaultdict(dict)
        # Find all less-specific prefixes
        # XXX Needs to be optimized
        for rtr_id in rib_bad_info:
            for index in rib_bad_info[rtr_id]:
                (pfxstr_min, pfxstr_max, rib_tup) = rib_bad_info[rtr_id][index]
                # Add the invalid route to the consolidated list
                consolidated[rtr_id][index] = ("I", rib_tup, mismatch[rtr_id][index])
                covering = self.aggregator.get_covering(rtr_id, pfxstr_min, pfxstr_max)
                # Add the covering routes to the consolidated list
                for (idx, status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop,
                     metric, locpref, weight, pathbutone, orig_asn,
                     route_orig) in covering:
                    rib_tup = (status, pfx, pfxlen, pfxstr_min,
                            pfxstr_max, nexthop, metric, locpref,
                            weight, pathbutone, orig_asn, route_orig)
                    if idx in consolidated[rtr_id]:
                        continue
                    elif idx in rib_good_info[rtr_id]:
                        consolidated[rtr_id][idx] = ("V", rib_good_info[rtr_id][idx], [])
                    else:
                        consolidated[rtr_id][idx] = ("-", rib_tup, [])
        return consolidated


class EOMEngine:
    """The analyzer module for EOM."""

    default_timeout = 30

    def __init__(self, args):
        """Instantiate the EOM analyzer object.

        Args:
            args: A namespace of arguments. 
                rpki_serv provides a list of arguments for any rpki-rtr pollers
                rtr_rib provides a list of arguments for any router rib pollers
        """
        self.fetchers = []
        self.aggregator = EOMAggregator(args.sql_database)
        self.analyzer = EOMAnalyzer(self.aggregator)
        self.reporter = EOMReporter()
        self.continuous = args.continuous
        # Add pollers based on the args
        if args.rpki_serv:
            for r in args.rpki_serv:
                self.add_rpkirtr_fetcher(r)
        if args.rtr_rib:
            for r in args.rtr_rib:
                self.add_rtr_rib_fetcher(r)

    def process_fetchers(self, now):
        """Process list of pollers and fetch data.

        Args:
            now: current timestamp

        Returns:
            A tuple containing the number of pending pollers and the
            earliest wakeup time. If there are no pollers in the queue,
            then both elements in the list are -1.
        """
        wakeup = now + EOMEngine.default_timeout
        if len(self.fetchers) == 0:
            return (-1, -1)
        tp = 0
        for f in self.fetchers:
            (pending, nextwake) = f.poll(now)
            if pending:
                tp += 1
                if nextwake < wakeup:
                    wakeup = nextwake
        return (tp, wakeup)
        
    def add_rpkirtr_fetcher(self, rpkirtr_args):
        """Add a new rpkirtr poller instance.

        Args:
            rpkirtr_args: Arguments for the EOMRPKIRtrCli instance. 

        Returns:
            None
        """
        f = EOMRPKIRtrCli(rpkirtr_args, self.aggregator)
        self.fetchers.append(f)

    def add_rtr_rib_fetcher(self, rtrrib_args):
        """Add a new rtr_rib poller instance.

        Args:
            rtrrib_args: Arguments for the EOMRtrRIBFetcher instance. 

        Returns:
            None
        """
        f = EOMRtrRIBFetcher(rtrrib_args, self.aggregator)
        self.fetchers.append(f)


    def run(self):
        """Kick off the analyzer process loop.

        Process all pollers, once we have all data run the analysis
        routine and repeat the loop.

        Args:
            None

        Returns:
            None
        """
        try:
            wakeup = None
            while True:
                now = Timestamp.now()
                wokeup = wakeup
                (pending, wakeup) = self.process_fetchers(now)
                if wakeup == -1:
                    print "Nothing to process."
                    break
                remaining = wakeup - now
                if pending:
                    print "Waiting for " + str(remaining)
                    asyncore.loop(timeout = remaining, count = 1)
                else:
                    result = self.analyzer.analyze()
                    self.reporter.show(result)
                    if not self.continuous:
                        break
                    print "sleeping for " + str(remaining)
                    time.sleep(remaining)
                print "Wokeup ... "
        except KeyboardInterrupt:
            sys.exit(0)
        finally:
            for f in self.fetchers:
                f.cleanup()

def rpki_server_spec(s):
    """Define the format for the rpki-server spec argument"""
    try:
        proto, host, port, force, reset = map(str, s.split(':'))
        n = argparse.Namespace()
        n.protocol = proto
        n.host = host
        n.port = int(port)
        # There is no database per channel, but we need to define the
        # parameter in the namespace
        n.sql_database = None
        if force == '-1':
            n.force_version = None 
        else:
            n.force_version = int(force) 
            if n.force_version not in PDU.version_map:
                raise argparse.ArgumentTypeError("Unrecognized Version")
        n.reset_session = True if reset == 'Y' else False 
        return n
    except:
        raise argparse.ArgumentTypeError("Format must be protocol:host:port:forceversion:reset")
             
def rtr_rib_spec(s):
    """Define the format for the rtr-rib spec argument"""
    try:
        device, poll_interval,reset,realm = map(str, s.split(':'))
        n = argparse.Namespace()
        n.device = device
        n.poll_interval = int(poll_interval)
        n.reset_session = True if reset == 'Y' else False 
        n.realm = realm
        return n
    except:
        raise argparse.ArgumentTypeError("Format must be device:poll_interval:reset")

def eom_parse_args(desc):
    parser = argparse.ArgumentParser(description = desc)
    parser.add_argument("--sql-database", help = "filename for sqlite3 database of EOM state")
    parser.add_argument("--rpki-serv", help="RPKI server spec", action="append", type=rpki_server_spec)
    parser.add_argument("--rtr-rib", help="Router spec", action="append", type=rtr_rib_spec)
    parser.add_argument("--debug", action = "store_true", help = "debugging mode")
    parser.add_argument("--log-level", default = "debug", 
                        choices = ("debug", "info", "warning", "error", "critical"),
                        type = lambda s: s.lower())
    parser.add_argument("--log-to", choices = ("syslog", "stderr"))
    parser.add_argument("--continuous", action = "store_true", help = "Keep polling continuously")
    return parser

