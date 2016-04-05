EOM Installation
================

Dependencies
------------

The following packages must be installed prior to installation of the
eom package.

* sqlite3
* os
* trigger
* asyncore
* argparse
* sys
* time
* collections
* pprint
* json
* rpki.rtr
* subprocess
* re
* netaddr
* pipes
* pyparsing
* logging

Installing a patched version of rpki-rtr
----------------------------------------

EOM also needs a couple of changes to be made to the rpki.rtr code. Util
these changes are merged into the main rpki.net software distribution,
the patch in the patches directory need to be applied by hand.


Trigger setup
-------------

EOM assumes that the operator already has a pre-configured Trigger setup
for router management. Information on configuring Trigger can be found
on https://trigger.readthedocs.org/en/latest

Installation of the EOM package (with CLI tools)
------------------------------------------------

The package can be installed by running the setup.py script as follows

::

    $ python setup.py install


Installation of EOM UI
----------------------

The EOM tool comes with a Django-based GUI. Currently this interface is
mainly for viewing EOM results and cannot be used to configure the EOM
tool.

In order to run the Django app in production it must be installed in
conjunction with an existing webserver instantiation. The specific
instructions for setting this up is out of scope for this document, but
may be found online. For example, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/modwsgi/

In order to run the Django app in test mode the following command may be
used:

::

    $ cd EOM-dist/eom_ui
    $ python manage.py runserver
    ...
    Starting development server at http://127.0.0.1:8000/
    Quit the server with CONTROL-C.


Note that the eom module needs to be configured first. See the
configuration section for instructions on configuring the EOM tool.


License
-------

* The EOM is distributed with a BSD-like license. See the LICENSE file for more information.

* The license information for the Trigger module is at https://trigger.readthedocs.org/en/latest/license.html

* The pyparsing module is distributed with a MIT license. See http://pyparsing.wikispaces.com/share/view/5698048


