#!/usr/bin/env python3
"""LocalPortManager - Setup Script"""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="localportmanager",
    version="1.0.3",
    author="SHAdd0WTAka",
    description="Zero-dependency local reverse proxy for managing services on dynamic ports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SHAdd0WTAka/LocalportManager",
    py_modules=["localportmanager"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "localportmanager=localportmanager:main",
            "lpm=localportmanager:main",
        ],
    },
)
