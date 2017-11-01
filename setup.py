#!/usr/bin/env/ python3

from setuptools import setup

setup(
    name='pyrocko-vagrant-bot',
    version='0.1',
    description='Simple Webhook Serving Mattermost',
    url='http://github.com/pyrocko/pyrocko-vagrant-bot',
    author='Marius Isken',
    author_email='info@pyrocko.org',
    license='GPL',
    test_suite='nose.collector',
    package_dir={
      'pyrocko_vagrant_bot': 'src',
    },
    packages=['pyrocko_vagrant_bot'],
    entry_points={
          'console_scripts':
          ['pyrocko-vagrant-bot = pyrocko_vagrant_bot.app:app']
    })
