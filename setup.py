# -*- coding: utf-8 -*-
import os
import re
import sys

from setuptools import find_packages, setup
"""
linux:
rm -rf "dist/*";rm -rf "build/*";python3 setup.py bdist_wheel;twine upload "dist/*;rm -rf "dist/*";rm -rf "build/*""
win32:
rm -r dist;rm -r build;python setup.py bdist_wheel;twine upload "dist/*";rm -r dist;rm -r build;rm -r uniparser.egg-info
"""

py_version = sys.version_info
if py_version.major < 3 or py_version.minor < 6:
    raise RuntimeError('Only support python3.6+')

with open('requirements.txt') as f:
    install_requires = [line for line in f.read().strip().split('\n')]

# for webui
if not re.search(r'requests|httpx|torequests|\[all\]', str(sys.argv)):
    install_requires.append('requests')

with open("README.md", encoding="u8") as f:
    long_description = f.read()

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'uniparser', '__init__.py'), encoding="u8") as f:
    version = re.search(r'''__version__ = ['"](.*?)['"]''', f.read()).group(1)

keywords = "requests crawler parser tools universal lxml beautifulsoup bs4 jsonpath udf toml yaml"
description = "Provide a universal solution for crawler platforms. Read more: https://github.com/ClericPy/uniparser."

requests_requires = ['requests']
httpx_requires = ['httpx']
aiohttp_requires = ['aiohttp']
torequests_requires = ['torequests>=5.1.5']
parsers_requires = [
    'selectolax', 'jsonpath-rw-ext', 'objectpath', 'bs4', 'toml', 'pyyaml>=5.3',
    'lxml', 'jmespath'
]
web_requires = ['fastapi', 'jinja2', 'uvicorn', 'uvloop', 'aiofiles']
all_requires = requests_requires + httpx_requires + torequests_requires + aiohttp_requires + parsers_requires
setup(
    name="uniparser",
    version=version,
    keywords=keywords,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT License",
    install_requires=install_requires,
    py_modules=["uniparser"],
    package_data={'uniparser': ['templates/*.html', 'static/*.js']},
    extras_require={
        'requests': requests_requires,
        'httpx': httpx_requires,
        'aiohttp': aiohttp_requires,
        'torequests': torequests_requires,
        'webparsers': parsers_requires,
        'all': all_requires,
        'web': web_requires
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    author="ClericPy",
    author_email="clericpy@gmail.com",
    url="https://github.com/ClericPy/uniparser",
    packages=find_packages(),
    platforms="any",
)
