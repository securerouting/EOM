
EOM Examples
============

A typical execution of EOM would resemble the following:

    $ python eom --sql-database eom_db.sqlite --rtr-rib router1:60:F \
        --rpki-serv tcp:localhost:8282:0:F

Here:

* 'router1' refers to the device ID for our router in the Trigger configuration.

* 'localhost' (8282) refers to the host (port) on which we have a running instance of the rpki-rtr manager.

* 'eom_db.sqlite' is the database within which RPKI and RIB information is saved.


A sample output might look like the following:

::

 - : *>i 10.0.0.0/8  192.168.1.1 0   0   0   1 2 422 i
 I : *>i 10.0.0.0/22 192.168.1.2 0   0   0   1 2 42  i
     [(42, '10.0.0.0/[16-20]'), (6, '10.0.0.0/[16-24]')]
 V : *>i 10.0.0.0/24 192.168.1.2 0   0   0   1 2 6   i
 I : *>i 10.0.0.0/26 192.168.1.3 0   0   0   1 2 6   i
     [(42, '10.0.0.0/[16-20]'), (6, '10.0.0.0/[16-24]')]


In this output the leading prefix may be one of '-' for unknown, 'V' for
valid and 'I' for invalid routes. The output above indicates that 
the routes for 10.0.0.0/22 and 10.0.0.0/26 are invalid because 1) the ROA for
10.0.0.0/[16-20] does not cover the prefix length and 2) the ROA
10.0.0.0/[16-24] while covering the prefix length has a different
origination ASN than the one in the route.

The output indicates that a router that performs RPKI validation may
prefer the route for /24 even though a route for the /26 prefix exists.
In this case since the paths are the same it makes no difference.
However in the case of the /22 route, the route that may be preferred
may be the one for the /8 aggregate, which originates from a different
ASN (422). 

