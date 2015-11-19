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


Installation
------------

The package can be installed by running the setup.py script as follows::

    $ python setup.py install

