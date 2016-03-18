"""Implementation of the analyzer module for EOM.

This module parses the arguments for EOM, either from the command line
or from a config file. The arguments passed on the command line takes
precedence over the arguments read from the config file (the config file
provides the defaults).
"""

import argparse
import yaml
from rpki.rtr.pdus import PDU

class rpki_server_spec:

    keys = ['proto', 'host', 'port', 'force', 'reset']

    def __init__(self):
        pass

    @staticmethod
    def sanitize(d):
        if not all (k in d for k in rpki_server_spec.keys):
            raise argparse.ArgumentTypeError("Incomplete rpki server spec")
        try:
            n = argparse.Namespace()
            n.protocol = d['proto']
            n.host = d['host']
            n.port = int(d['port'])
            # There is no database per channel, but we need to define the
            # parameter in the namespace
            n.sql_database = None
            if d['force'] == '-1':
                n.force_version = None 
            else:
                n.force_version = int(d['force']) 
                if n.force_version not in PDU.version_map:
                    raise argparse.ArgumentTypeError("Unrecognized Version")
            n.reset_session = True if d['reset'] == 'Y' else False 
            return n
        except:
            raise argparse.ArgumentTypeError("Badly formatted rpki server spec")

    def __call__(self, s):
        """Define the format for the rpki-server spec argument"""
        try:
            d = dict(zip(rpki_server_spec.keys, map(str, s.split(':'))))
        except:
            raise argparse.ArgumentTypeError("Format must be protocol:host:port:forceversion:reset")
        return rpki_server_spec.sanitize(d) 
       

class rtr_rib_spec:

    keys = ['device', 'poll_interval', 'reset', 'realm']

    def __init__(self):
        pass

    @staticmethod
    def sanitize(d):
        if not all (k in d for k in rtr_rib_spec.keys):
            raise argparse.ArgumentTypeError("Incomplete rpki server spec")
        try:
            n = argparse.Namespace()
            n.device = d['device']
            n.poll_interval = int(d['poll_interval'])
            n.reset_session = True if d['reset'] == 'Y' else False 
            n.realm = d['realm']
            return n
        except:
            raise argparse.ArgumentTypeError("Badly formatted rtr_rib spec")

    def __call__(self, s):
        """Define the format for the rtr-rib spec argument"""
        try:
            d = dict(zip(rtr_rib_spec.keys, map(str, s.split(':'))))
        except:
            raise argparse.ArgumentTypeError("Format must be device:poll_interval:reset:realm")
        return rtr_rib_spec.sanitize(d) 


def eom_setup_parser(desc):
    """Define command line arguments"""

    parser = argparse.ArgumentParser(description = desc)
    parser.add_argument("--config_file", help = "Config file for EOM.", type=argparse.FileType('r'))
    parser.add_argument("--sql-database", help = "filename for sqlite3 database of EOM state")
    parser.add_argument("--init-db", help = "Initialize the DB tables", action='store_true')
    parser.add_argument("--rpki-serv", help="RPKI server spec", action="append", type=rpki_server_spec())
    parser.add_argument("--rtr-rib", help="Router spec", action="append", type=rtr_rib_spec())
    parser.add_argument("--debug", action = "store_true", help = "debugging mode")
    parser.add_argument("--log-level", default = "debug", 
                        choices = ("debug", "info", "warning", "error", "critical"),
                        type = lambda s: s.lower())
    parser.add_argument("--log-to", choices = ("syslog", "stderr"))
    parser.add_argument("--continuous", action = "store_true", help = "Keep polling continuously")
    return parser


def eom_parse_args(desc):
    """Parse arguments (CLI or config file) and return the dict"""
    parser = eom_setup_parser(desc)
    args = parser.parse_args()
    if args.config_file:
        yamldata = yaml.load(args.config_file)
        delattr(args, 'config_file')
        arg_dict = args.__dict__

        # Use rpki_serv from file if value not provided in CL
        if 'rpki_serv' in yamldata and not arg_dict['rpki_serv']:
            rpki_serv_args = []
            if isinstance(yamldata['rpki_serv'], list):
                for r in yamldata['rpki_serv']:
                    rpki_serv_args.append(rpki_server_spec.sanitize(r))
            else:
                rpki_serv_args.append(rpki_server_spec.sanitize(yamldata['rpki_serv']))
            args.rpki_serv = rpki_serv_args

        # Use rtr_rib from file if value not provided in CL
        if 'rtr_rib' in yamldata and not arg_dict['rtr_rib']:
            rtr_rib_args = []
            if isinstance(yamldata['rtr_rib'], list):
                for r in yamldata['rtr_rib']:
                    rtr_rib_args.append(rtr_rib_spec.sanitize(r))
            else:
                rtr_rib_args.append(rtr_rib_spec.sanitize(yamldata['rtr_rib']))
            args.rtr_rib = rtr_rib_args

        # Use sql_database from file if value not provided in CL
        if 'sql_database' in yamldata and not arg_dict['sql_database']:
            args.sql_database = yamldata['sql_database']

    return args
