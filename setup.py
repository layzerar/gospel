# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name="gospel",
    version="0.1",
    description="Utilities for deploying applications",
    author="Melvi Ts",
    author_email="layzerar@gmail.com",
    url="https://github.com/layzerar/gospel",
    license="MIT License",
    packages=['gospel'],
    scripts=[
        'scripts/gossc',
    ],
    zip_safe=True,
    install_requires=[
        'psutil>=1.2.1',
    ],
    classifiers=[
        'Private :: Do Not Upload',
    ],
)
