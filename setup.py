# -*- coding: utf-8 -*-
import os
import re

from setuptools import find_packages, setup
"""
linux:
rm -rf "dist/*";rm -rf "build/*";python3 setup.py bdist_wheel;twine upload "dist/*;rm -rf "dist/*";rm -rf "build/*""
win32:
rm -rf dist;rm -rf build;python3 setup.py bdist_wheel;twine upload "dist/*";rm -rf dist;rm -rf build;rm -rf uniparser.egg-info
"""

install_requires = [
    'jsonpath_ng',
    'objectpath',
    'bs4',
    'toml',
    'pyyaml',
    'lxml',
]

with open("README.md", encoding="u8") as f:
    long_description = f.read()

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'uniparser', '__init__.py'), encoding="u8") as f:
    version = re.search(r'''__version__ = ['"](.*?)['"]''', f.read()).group(1)

setup(
    name="uniparser",
    version=version,
    keywords=(
        "requests async multi-thread aiohttp asyncio uvloop asynchronous"),
    description=
    "Provide a universal solution for crawler platforms. Read more: https://github.com/ClericPy/uniparser.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT License",
    install_requires=install_requires,
    py_modules=["uniparser"],
    extras_require={},
    author="ClericPy",
    author_email="clericpy@gmail.com",
    url="https://github.com/ClericPy/uniparser",
    packages=find_packages(),
    platforms="any",
)
