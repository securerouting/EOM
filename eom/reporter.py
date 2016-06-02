"""Implementation of generic reporter module for EOM.

This module implements a generic reporter module that interfaces with
the User Interface (currently stdout).
"""
class EOMReporter:
    """A generic reporter module"""
    def __init__(self):
        """Instantiate the reporter object.

        Args:
            None.
        """
        pass

    def get_rib_display_str(self, rib_tup):
        """Get a string representation for the RIB tuple
        
        Args:
            rib_tuple: A tuple containing RIB information

        Returns:
            A string representation for the tuple.
        """
        (status, pfx, pfxlen, pfxstr_min, pfxstr_max, nexthop, metric,
         locpref, weight, pathbutone, orig_asn, route_orig) = rib_tup
        if pathbutone == "":
            pathstr = str(orig_asn)
        else:
            pathstr = pathbutone + " " + str(orig_asn)
        metstr = str(metric) if metric >= 0 else ""
        lpstr = str(locpref) if locpref >= 0 else ""
        wtstr = str(weight) if weight >= 0 else ""
        return status + "\t" + pfx + "/" + str(pfxlen) + "\t" + \
               nexthop + "\t" + metstr + "\t" + \
               lpstr + "\t" + wtstr + "\t" + \
               pathstr + "\t" + route_orig

    def show(self, data, ts):
        """Display data onto the User Interface

        Args:
            data(dict): An object containing particulars of the data to
                        be displayed. 

        Returns:
            status(boolean): True if success; False if failure.

        """
        for rtr in data:
            print "\nTest run at: " + str(ts)
            print "Router: " + str(rtr) 
            print "   " + "\t" + "Network" + "   " + "\t" + "Next Hop" + \
                "\t" + "Metric" + "\t" + "LocPrf" + "\t" + "Weight" + \
                "\t" + "Path"
            for (i, v) in sorted(data[rtr].items(), key=lambda x:int(x[0])):
                print v[0] + " : " + self.get_rib_display_str(v[1])
                if v[2]:
                    for (host, port, asn, prefix, prefixlen, max_prefixlen) in v[2]:
                        rpkirtrpfxstr = str(asn) + ":" + prefix + "/" + "[" + str(prefixlen) + '-' + str(max_prefixlen) + "]"
                        print "\t" + host + ":" + port + ": " + rpkirtrpfxstr
