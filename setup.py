#!/usr/bin/env python

from setuptools import setup
from settings import VERSION
from phat_main.main import AutoTest

plugins = AutoTest.load_plugins()

pkgs = ['plugins.' + pl.__name__.split('.')[0] for pl in plugins] + ['phat_main', 'common']

setup(name='phat-tool',
      version=VERSION,
      description='Pluggable HTTP Auto Testing',
      author='Daniel Franca',
      url='https://github.com/danielfranca/phat',
      license='MIT',
      packages=pkgs,
      install_requires=['python-Levenshtein>=0.11.2', 'beautifulsoup4>=4.4.1', 'requests>=2.5.0', 'paramiko>=1.15.2', 'jsonpath-rw>=1.4.0', 'selenium>=2.53.2', 'responses>=0.5.1'],
      scripts=['phat', 'settings.py'],)
