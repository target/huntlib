#!/usr/bin/env python

from setuptools import setup

setup(name='huntlib',
      version='0.1',
      description='A Python library to help with some common threat hunting data analysis operations',
      url='https://github.com/target/huntlib',
      author='David J. Bianco',
      author_email='david.bianco@target.com',
      packages=['huntlib'],
      tests_require=['pytest'],
      setup_requires=['pytest-runner'],
      install_requires=[
        'future',
        'splunk-sdk',
        'elasticsearch-dsl',
        'pandas',
        'numpy'
      ],
      zip_safe=True
)
