#!/usr/bin/env python

from setuptools import setup
from settings import VERSION
from main.main import AutoTest

plugins = AutoTest.load_plugins()

pkgs = ['plugins.' + pl for pl in plugins] + ['main', 'common']

setup(name='PHAT',
      version=VERSION,
      description='Pluggable HTTP Auto Testing',
      author='Daniel Franca',
      author_email='daniel.franca@gmail.com',
      packages=pkgs,
      install_requires=['python-Levenshtein==0.11.2', 'beautifulsoup4==4.4.1', 'requests==2.4.0', 'paramiko==1.15.2', 'jsonpath-rw==1.4.0', 'selenium==2.53.2', 'responses==0.5.1'],
      scripts=['phat', 'settings.py'],
)
