"""Implementation of a generic poller.

This module implements an abstract class that serves as the base class
for all poller modules. This includes an event queue that keeps track of
events that are to be processed during the current time instance
and the maintenance of the event log associated with all poll
operations.
"""

import netaddr

class EOMGenericPoller:
    """A generic poller"""
    def __init__(self, conf, aggregator):
        """Instantiate the generic poller object.

        Args:
            conf(dict): Configuration parameters for the client
            aggregator(EOMAggregator): The data aggregator object
        """
        pass

    def cleanup(self):
        """Clean up at exit time.
            
        This method must be overridden by sub-classes.
        """
        pass

    def poll(self):
        """poll the associated device 
            
        This method must be overridden by sub-classes.
        """
        pass

    @staticmethod
    def get_ip_str(ipint):
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

