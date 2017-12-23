#!/usr/bin/python
from setuptools import setup, find_packages

setup(
    name = "python-idzip",
    version = "0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "idzip = idzip.command:main"
        ]
    }
)
