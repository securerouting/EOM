
EOM CLI Examples
=================

Command Line Usage
------------------

A typical execution of EOM would resemble the following:

::

    $ python eom --sql-database eom_db.sqlite \
        --rtr-rib router1:86400:N:local \
        --rpki-serv tcp:localhost:8282:0:N


See the configuration section for additional details on what these
options mean.

A configuration file may also be passed to the EOM CLI in lieu of
passing the three options listed above. An example invocation of eom
with a configuration file is:

::

    $ python eom --config_file eom_config.yml


See the configuration section for addition details on the yml
configuration file.


Command Line Output
-------------------

A sample output might look like the following:

::

 - : *>i    10.0.0.0/8    192.168.1.1    0    0    0    1 2 422    i
 I : *>i    10.0.0.0/22    192.168.1.2    0    0    0    1 2 42    i
     (localhost:1234) 6:10.0.0.0/[16-24]
     (localhost:1234) 42:10.0.0.0/[16-20]
 V : *>i    10.0.0.0/24    192.168.1.2    0    0    0    1 2 6    i
     (localhost:1234) 6:10.0.0.0/[16-24]
 I : *>i    10.0.0.0/26    192.168.1.3    0    0    0    1 2 6    i
     (localhost:1234) 6:10.0.0.0/[16-24]
     (localhost:1234) 42:10.0.0.0/[16-20]

In this output the leading prefix may be one of '-' for unknown, 'V' for
valid and 'I' for invalid routes. The output above indicates that 
the routes for 10.0.0.0/22 and 10.0.0.0/26 are invalid because 1) the ROA for
10.0.0.0/[16-20] does not cover the prefix length and 2) the ROA
10.0.0.0/[16-24] while covering the prefix length has a different
origination ASN than the one in the route. 'localhost:1234' refers to
the RPKI Router server that was used as the source for the ROAs.

The output indicates that a router that performs RPKI validation may
prefer the route for /24 even though a route for the /26 prefix exists.
In this case since the paths are the same it makes no difference.
However in the case of the /22 route, the route that may be preferred
may be the one for the /8 aggregate, which originates from a different
ASN (422). 

