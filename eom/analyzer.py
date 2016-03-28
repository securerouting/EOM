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

    def analyze(self, ts):
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
        matched = defaultdict(dict)

        toprocess = self.aggregator.get_rpki_rib()
        for (device, index, asn, prefix, prefixlen, max_prefixlen, 
                status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop,
                metric, locpref, weight, pathbutone, orig_asn,
                route_orig) in toprocess:
            
            # The RPKI prefix must contain the advertised prefix
            if pfxlen < prefixlen:
                continue

            # Create a RIB entry tuple
            rib_tup = (status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop,
                       metric, locpref, weight, pathbutone, orig_asn, route_orig)

            if asn == orig_asn and pfxlen <= max_prefixlen:
                if index in rib_bad_info[device]:
                    del rib_bad_info[device][index]
                if index in mismatch[device]:
                    del mismatch[device][index]
                rib_good_info[device][index] = rib_tup
                if index in matched[device]:
                    matched[device][index].append((asn, prefix, prefixlen, max_prefixlen))
                    matched[device][index] = list(set(matched[device][index]))
                else:
                    matched[device][index] = [(asn, prefix, prefixlen, max_prefixlen)]
            elif index not in rib_good_info[device]:
                rib_bad_info[device][index] = (pfxstr_min, pfxstr_max, rib_tup)
                if index in mismatch[device]:
                    mismatch[device][index].append((asn, prefix, prefixlen, max_prefixlen))
                    mismatch[device][index] = list(set(mismatch[device][index]))
                else:
                    mismatch[device][index] = [(asn, prefix, prefixlen, max_prefixlen)]

        # return all affected paths
        consolidated = defaultdict(dict)
        # Find all less-specific prefixes
        # XXX Needs to be optimized
        for device in rib_bad_info:
            for index in rib_bad_info[device]:
                (pfxstr_min, pfxstr_max, rib_tup) = rib_bad_info[device][index]
                # Add the invalid route to the consolidated list
                consolidated[device][index] = ("I", rib_tup, mismatch[device][index])
                covering = self.aggregator.get_covering(device, pfxstr_min, pfxstr_max)
                # Add the covering routes to the consolidated list
                for (idx, status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop,
                     metric, locpref, weight, pathbutone, orig_asn,
                     route_orig) in covering:
                    if idx in consolidated[device]:
                        continue
                    elif idx in rib_good_info[device]:
                        consolidated[device][idx] = ("V", rib_good_info[device][idx], matched[device][idx])
                    else:
                        rib_tup = (status, pfx, pfxlen, pfxstr_min,
                                   pfxstr_max, nexthop, metric, locpref,
                                   weight, pathbutone, orig_asn, route_orig)
                        consolidated[device][idx] = ("-", rib_tup, [])
        self.aggregator.store_analysis_results(consolidated, ts)
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
        self.aggregator = EOMAggregator(args.sql_database, args.init_db)
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
                    ts = int(now)
                    result = self.analyzer.analyze(ts)
                    self.reporter.show(result, ts)
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
