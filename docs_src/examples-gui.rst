
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

