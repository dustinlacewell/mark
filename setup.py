#!/usr/bin/env python

from setuptools import setup

setup(
    name='mark',
    version='0.1.0',
    description='command-line db query and graphing tool',
    author='Dustin Lacewell',
    author_email='dlacewell@gmail.com',
    url='https://github.com/dustinlacewell/mark',
    packages=['mark'],
    install_requires=[
        'click',
        'bashplotlib',
        'blessings',
        'psycopg2',
        'tabulate',
        'pyYAML',
    ],
    entry_points={
        'console_scripts': [
            'mark = mark.cli:main',
        ],
    }
)
