
EOM CLI Examples
=================

Command Line Usage
------------------

A typical execution of EOM would resemble the following:

    $ python eom --sql-database eom_db.sqlite --rtr-rib router1:60:F \
        --rpki-serv tcp:localhost:8282:0:F

Here:

* 'router1' refers to the device ID for our router in the Trigger configuration.

* 'localhost' (8282) refers to the host (port) on which we have a running instance of the rpki-rtr manager.

* 'eom_db.sqlite' is the database within which RPKI and RIB information is saved.


A configuration file may also be passed to the EOM CLI in lieu of
passing the three options listed above. An example invocation of eom
with a configuration file is:

    $ python eom --config_file eom_config.yml


See the configuration section for addition details on the yml
configuration file.


Command Line Output
-------------------

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

EOM GUI Examples
=================

The following examples assume that the Django app is running on
127.0.0.1:8000

Status Summary
--------------

This page gives a summary of the error reports availble.

.. image:: /images/EOM-UI-Status.png
   :height: 500px
   :width: 1000px


The report Id links to the detailed report corresponding to the given
entry.

The Device name corresponds to the device identifier that was specified
in the Trigger configuration

The timestamp specifies the time of creation of the report.

The Invalid field specifies that number of routes that were found to be
invalid in the given report. The actual invalid routes can be viewed by
looking at the detailed report.


Detailed Report
---------------

This page provides details on the routes that were found to be invalid for
the given device, any covering routes that were found to be valid or
unspecified, and the constraints that were either violated or satisfied
for the given prefix and ASN combination. 

.. image:: /images/EOM-UI-Status-Detail.png
   :height: 500px
   :width: 1000px

The ROA status can be one of the following:

    ✅  : The ROA constraints matched 
    ❌  : The ROA constraints did not match
    ?  : No ROA matching the give prefix was found 

