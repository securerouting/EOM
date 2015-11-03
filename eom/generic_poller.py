"""Implementation of a generic poller.

This module implements an abstract class that serves as the base class
for all poller modules. This includes an event queue that keeps track of
events that are to be processed during the current time instance
and the maintenance of the event log associated with all poll
operations.
"""

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
