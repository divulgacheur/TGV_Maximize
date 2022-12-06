#!/usr/bin/env python3

from distutils.core import setup

setup(name='TGV_Maximize',
      version='2.0',
      description='CLI client to show all available tickets for MAXJeunes subscription',
      author='Divulgacheur',
      author_email='github@theopeltier.me',
      packages=['argcomplete', 'chardet','distutils','pyhafas','pylint','python-dotenv', 'requests','Unidecode']
      )
