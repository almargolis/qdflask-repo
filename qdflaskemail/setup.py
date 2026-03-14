"""
Setup script for qdflaskemail package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qdflaskemail",
    version="0.1.0",
    author="Albert Margolis",
    author_email="almargolis@gmail.com",
    description="Email notification service for QuickDev Flask applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/almargolis/quickdev",
    project_urls={
        "Bug Tracker": "https://github.com/almargolis/quickdev/issues",
        "Documentation": "https://github.com/almargolis/quickdev/blob/master/qdflaskemail/README.md",
        "Source Code": "https://github.com/almargolis/quickdev/tree/master/qdflaskemail",
    },
    license="MIT",
    package_dir={'': 'src'},
    packages=['qdflaskemail'],
    include_package_data=True,
    package_data={
        'qdflaskemail': ['qd_conf.toml'],
    },
    install_requires=[
        "Flask>=2.0.0",
        "qdemail",
        "qdflask",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Framework :: Flask",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
