#!/usr/bin/env python

import sys
#from distutils.core import setup
from setuptools import setup

rh = open('README', 'r')
long_description = rh.read()
rh.close()

setup(name='EOM',
      version='1.3',
      description='Emulation and Operation Monitoring (EOM) Tool',
      author='Suresh Krishnaswamy',
      author_email='suresh@tislabs.com',
      url='https://securerouting.net',
      license='See LICENSE',
      long_description=long_description,
      packages=['eom'],
      scripts=['eom/eom', 'eom/do_poll.py'],
      platforms='any',
      install_requires=[
#        'sqlite3',
#        'os',
#        'trigger',
#        'asyncore',
#        'argparse',
#        'sys',
#        'time',
#        'collections',
#        'pprint',
#        'json',
#        'rpki.rtr',
#        'subprocess',
#        're',
#        'netaddr',
#        'pipes',
#        'pyparsing',
#        'logging',
      ],
     )
