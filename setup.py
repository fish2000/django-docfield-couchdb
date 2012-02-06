#/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys, os
sys.path.append(os.getcwd())

import version

setup(
    name='django-docfield-couchdb',
    version='0.1.0',
    description="Django fields for representing CouchDB docs and more.",
    long_description="""
    
    Django fields and other add-ons that represent key CouchDB data structures:
    
    *) Docs, which can authoratively reside in either Couch or your Django RDBMS
    *) Arbitrary JSON subtrees
    *) CouchDB _id and _rev identifiers
    
    And MORE! Coming soon of course. (next up, JSON diff views and widgets!)
    
    """,
    author=version.__author__,
    author_email='fish2000@gmail.com',
    maintainer=version.__author__,
    maintainer_email='fish2000@gmail.com',
    license='BSD',
    url='http://github.com/fish2000/django-docfield-couchdb/',
    download_url='https://github.com/fish2000/django-docfield-couchdb/zipball/master',
    keywords=[
        'django',
        'couchdb',
        'json',
        'NoSQL',
        'database',
        'utility',
        'fields',
        'models',
        'trees',
        'fields',
    ],
    install_requires=[
        'couchdbkit',
        'simplejson',
    ],
    packages=[
        'docfield',
    ],
    classifiers=[
    'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Environment :: Other Environment',
        'Environment :: Plugins',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
        'Topic :: Utilities',
    ]
)

