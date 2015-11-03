"""Implementation of the rpki-rtr client function for EOM.

This module interfaces with a rpki-rtr server component to retrieve
validated RPKI information for use by routers. The received data is
saved through the aggregator module to an internal data store.
"""

import asyncore
from rpki.rtr.client   import ClientChannel
from rpki.rtr.channels import Timestamp
from rpki.rtr.pdus     import ResetQueryPDU, SerialQueryPDU

from eom.generic_poller import EOMGenericPoller

ClientChannelClass = ClientChannel

class EOMRPKIRtrCli(EOMGenericPoller):
    """Poller for fetching RPKI prefix information from an RPKI-Rtr Manager instance"""
    def __init__(self, args, aggregator):
        """Instantiate the rpki-rtr client object.

        Args:
            conf(dict): Configuration parameters for the client
            aggregator(EOMAggregator): The data aggregator object
        """
        assert aggregator != None
        if args.reset_session:
            aggregator.reset_rpki_rtr_session(args.host, args.port)
        constructor = getattr(ClientChannelClass, args.protocol)
        self.client = constructor(args)
        sql = aggregator.get_sql_connection()
        self.client.set_sql_connection(sql)
        self.client.update_session()
        self.polled = self.client.updated

    def cleanup(self):
        """Clean up the client object associated with the poller.

        Args:
            None

        Returns:
            None
        """
        self.client.cleanup()

    def poll(self, now):
        """Poll data from configured RPKI-rtr server instances.

        Process the queue to identfy events that must be processed
        during this time interval. 

        Args:
            now: current timestamp

        Returns:
            (Boolean, int): A tuple comprising of a pending status and
                            the timestamp for the next event in the queue.
        """
        # Check if we've either never polled or polled earlier than the last update
        if not self.polled or self.polled < self.client.updated:
            if self.client.serial is not None and now > self.client.updated + self.client.expire:
                logging.info("[Expiring client data: serial %s, last updated %s, expire %s]",
                             self.client.serial, self.client.updated, self.client.expire)
                self.client.cache_reset()

            if self.client.serial is None or self.client.nonce is None:
                self.polled = now
                self.client.push_pdu(ResetQueryPDU(version = self.client.version))

            elif now >= self.client.updated + self.client.refresh:
                self.polled = now
                self.client.push_pdu(SerialQueryPDU(version = self.client.version,
                                                    serial  = self.client.serial,
                                                    nonce   = self.client.nonce))

        # Find how long we must wait 
        timer = self.client.retry if (now >= self.client.updated + self.client.refresh) else self.client.refresh
        wakeup = max(now, Timestamp(max(self.polled, self.client.updated) + timer))
        remaining = wakeup - now
        # Find if we're still waiting for data to arrive
        pending = True if self.client.updated < self.polled else False 
        return (pending, wakeup)

