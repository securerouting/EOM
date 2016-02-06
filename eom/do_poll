#!/usr/bin/python

""" Fetch RIB information from routers.

This scripts queries the given device for its RIB information using the
'sh ip bgp' command. The script assumes that one of either Trigger or
RANCID has been configured in order to enable the router to authenticate
the issuance of such commands from the querying machine.

NOTE: That RANCID support appears to be not fully supported in Trigger,
so this does not seem to work properly at the moment.

The output is returned as a JSON representation of a dict structure,
indexed on the device name and the command run.

"""
from trigger import rancid,netdevices,cmds
import argparse
from pprint import pprint
import json
from subprocess import call

#RANCID_ROOT = '/path/to/rancid/routers'
RANCID_ROOT = '/Volumes/Secondary/tmp/rancid/routers'

class CommandWrapper():
    """Generic Command Wrapper Class.

    Allows us to poll the attached net devices for BGP information. 
    Note that this class must not be instantiated directly.
    """
    def __init__(self, devicenames):
        """Base class constructor.
        
        Args:
            devicenames(list of strs): A list of device names
        """
        self.command = 'show ip bgp'
        self.devicelist = []

    def poll(self):
        """Poll device list for BGP RIB information.

        Poll all the NetDevices that are associated with this object and
        query them for BGP RIB information using 'sh ip bgp'. The
        results are returned as a JSON string.

        Args:
            None.

        Returns:
            str: A JSON string representation of the results
        """
        c = cmds.Commando(devices=self.devicelist, commands=[self.command], verbose=False)
        c.run()
        return (json.dumps(c.results))

class RancidCommandWrapper(CommandWrapper):
    """Subclass for issuing router commands using RANCID"""
    def __init__(self, devicenames):
        """constructor.
       
        Initialize the RancidCommandWrapper object. Also convert the
        list of devices in devicenames to a list of Rancid NetDevices.

        Args:
            devicenames(list of strs): A list of device names
        """
        CommandWrapper.__init__(self, devicenames)
        r = rancid.Rancid(RANCID_ROOT)
        nd = r.devices
        for d in devicenames:
            if d in nd.keys():
                self.devicelist.append(nd[d])

class TriggerCommandWrapper(CommandWrapper):
    """Subclass for issuing router commands using Trigger"""
    def __init__(self, devicenames):
        """constructor.
       
        Initialize the TriggerCommandWrapper object. Also convert the
        list of devices in devicenames to a list of NetDevices.

        Args:
            devicenames(list of strs): A list of device names
        """
        CommandWrapper.__init__(self, devicenames)
        nd = netdevices.NetDevices(production_only=False)
        for d in devicenames:
            self.devicelist.append(nd.find(d))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", action="append", help="Device to lookup", required=True)
    parser.add_argument("--mode", choices=['trigger', 'rancid'], default='trigger', help="Mode of lookup")
    parser.add_argument("--rancidroot", default=RANCID_ROOT, help="Path to rancid root")
    args = parser.parse_args()

    r = {}
    try:
        if args.mode == 'trigger':
            c = TriggerCommandWrapper(args.device)
        else:
            c = RancidCommandWrapper(args.device)
        r = c.poll()
    except:
        pass

    print r

