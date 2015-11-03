"""This package contains scripts that enables an operator to assess the
impact of RPKI validation on routing.

This package exports the following classes:

EOMAggregator: A RPKI-Rtr and RIB data aggregator.
EOMAnalyzer: The analyzer module for EOM
EOMGenericPoller: A generic poller
EOMRPKIRtrCli: Poller for fetching RPKI prefix information from an RPKI-Rtr Manager instance
EOMRtrRIBFetcher: Poller for fetching RIB information from a router instance.
EOMReporter: A generic reporter module

CommandWrapper: Generic Command Wrapper Class
RancidCommandWrapper: Subclass for issuing router commands using RANCID
TriggerCommandWrapper: Subclass for issuing router commands using Trigger

"""
