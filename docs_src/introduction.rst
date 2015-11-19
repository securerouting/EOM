EOM  - An Emulation and Operations Monitoring Tool
==================================================

The purpose of this tool is to provide an emulation environment in which
an ISP (or other BGP AS) can analyze the impact of planned deployment of
RPKI validation in local conditions, without impacting their routing
operations. The EOM Tool is expected to assist the operator in scenarios
such as the following (note that not all of these features are
implemented yet).

* Assessing if the best route selection changes when validation is enabled.
* Assessing the manner in which the best path changes when different localpref/weight settings are used.
* Combining data from multiple routers in different ASNs to check for any routing-level inconsistencies.
* Assessing potential problems associated with validating prefixes in a multihoming environment.
* Assessing whether an ISP’s reliance on multiple rpki-rtr manager instances could result in routing-level inconsistencies.
* Testing custom prefix assignment and certification conditions for simulation of failures and other special scenarios - e.g. resource transfers.

