#!/usr/bin/env python
from setuptools import setup

import os

DESC = """Pyprocmail is a python parser and AST definitions for procmail's procmailrc files."""
with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()
data_files = []

setup(
    name='pyprocmail',
    version='0.1.1',
    description=DESC,
    long_description=README,
    author='Valentin Samir',
    author_email='valentin.samir@crans.org',
    license='GPLv3',
    url='https://github.com/nitmir/pyprocmail',
    download_url="https://github.com/nitmir/pyprocmail/releases",
    packages=['pyprocmail'],
    package_data={
    },
    keywords=['procmail', 'parser', 'procmailrc', 'AST', 'tree', 'syntax'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Communications :: Email :: Filters',
    ],
    install_requires=["pyparsing >= 2.0"],
    zip_safe=False,
)
