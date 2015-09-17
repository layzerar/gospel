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
        'Jinja2>=2.4',
    ],
    classifiers=[
        'Private :: Do Not Upload',
    ],
)
