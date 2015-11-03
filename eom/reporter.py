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
        return status + "\t" + pfx + "/" + str(pfxlen) + "\t" + \
               nexthop + "\t" + str(metric) + "\t" + \
               str(locpref) + "\t" + str(weight) + "\t" + \
               pathbutone + " " + str(orig_asn) + "\t" + route_orig

    def show(self, data):
        """Display data onto the User Interface

        Args:
            data(dict): An object containing particulars of the data to
                        be displayed. 

        Returns:
            status(boolean): True if success; False if failure.

        """
        for rtr in data:
            print "Router: " + str(rtr)
            for (i, v) in sorted(data[rtr].items(), key=lambda x:int(x[0])):
                print v[0] + " : " + self.get_rib_display_str(v[1])
                if v[2]:
                    print "\t" + str(v[2])
