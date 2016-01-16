# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


setup(
    name="gospel",
    version="0.1.4",
    description="Utilities for deploying applications",
    author="Melvi Ts",
    author_email="layzerar@gmail.com",
    url="https://github.com/layzerar/gospel",
    license="MIT License",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'gossc=gospel.scripts.gossc:main',
        ],
    },
    zip_safe=True,
    install_requires=[
        'psutil>=1.2.1',
    ],
    classifiers=[
        'Private :: Do Not Upload',
    ],
)
