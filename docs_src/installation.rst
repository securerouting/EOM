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


License
-------

* The EOM is distributed with a BSD-like license. See the LICENSE file for more information.

* The license information for the Trigger module is at https://trigger.readthedocs.org/en/latest/license.html

* The pyparsing module is distributed with a MIT license. See http://pyparsing.wikispaces.com/share/view/5698048


Installation
------------

The package can be installed by running the setup.py script as follows::

    $ python setup.py install

