
EOM Configuration
=================

There are two steps required as part of the EOM tool configuration. The
first is the database initialization step, while the second is defining
a configuration file for routine EOM operation. This section describes
both of these steps.

Database initialization
-----------------------

First initialize an empty database as follows

::

    $ cd EOM-dis/eom
    $ python eom --sql-database /path/to/db/eom_db.sqlite --init-db


Next, ensure that the eom_ui settings file references the correct
database file.

In EOM-dist/eom_ui/eom_ui/settings.py ensure that the DATABASES section
refers to the correct file. For example

::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join('/path/to/db', 'eom_db.sqlite'),
        }
    }

Finally, migrate the local database customizations to the above defined
DB file.

::

    $ cd EOM-dist/eom_ui
    $ python manage.py migrate


Defining the EOM configuration file
-----------------------------------

A sample EOM configuration file is shown below

::

    rtr_rib:
        device: quagga.vm
        poll_interval: 86400
        reset: N
        realm: local

    sql_database: /path/to/db/eom_db.sqlite

    rpki_serv:
        proto: tcp
        host: rpki-validator.realmv6.org
        port: 8282
        force: 0
        reset: N


The rtr_rib section specifies the device(s) that must be polled for RIB
information. 

Here:

* device refers to the device identifier for our router in the Trigger
  configuration.
* poll_interval specifies the duration that the EOM tool must wait
  between repeated queries to the router for RIB information.
* reset specifies whether the rtr_cache table is to be flushed prior to
  the initial poll operation.
* realm refers to the Trigger module realm that is associated with the
  credentials for this router device. 


The rpki_serv section specifies the rpki-rtr server(s) that must be
polled for RPKI information. 

* proto specifies the protocol to use for querying the rpki-rtr server
  instance.
* the host/port fields sepcify the location of the running rpki-rtr
  server instance.
* force specifies the version to use. Set this value to -1 if no
  particular version is to be forced.
* reset specifies whether the rtr_cache table is to be flushed prior to
  the initial poll operation.


Note that when executed from the command line, the rpki_serv and rtr_rib
options are specified through a ':' separated list of fields. That is,
the above configuration could be specified to the eom tool as follows:


::

    $python eom --sql-database /path/to/db/eom_db.sqlite \
               --rtr-rib quagga.vm:86400:N:local \
               --rpki-serv tcp:rpki-validator.realmv6.org:8282:0:N 


The above example shows a single rtr_rib and rpki_serv instance. If
multiple devices need to be specified the it could be done so as
follows:

::

    rtr_rib:
        - device: quagga.vm
          poll_interval: 86400
          reset: N
          realm: local 
        - device: quagga2.vm
          poll_interval: 86400
          reset: N
          realm: local

    sql_database: /path/to/db/eom_db.sqlite

    rpki_serv:
        - proto: tcp
          host: rpki-validator.realmv6.org
          port: 8282
          force: 0
          reset: N
        - proto: tcp
          host: ca0.rpki.net
          port: 43779
          force: -1 
          reset: N

