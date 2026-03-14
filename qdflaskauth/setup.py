"""
Setup script for qdflaskauth package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qdflaskauth",
    version="0.1.0",
    author="Albert Margolis",
    author_email="almargolis@gmail.com",
    description="Flask authentication routes, RBAC, and user management for QuickDev",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/almargolis/quickdev",
    project_urls={
        "Bug Tracker": "https://github.com/almargolis/quickdev/issues",
        "Documentation": "https://github.com/almargolis/quickdev/blob/master/qdflaskauth/README.md",
        "Source Code": "https://github.com/almargolis/quickdev/tree/master/qdflaskauth",
    },
    license="MIT",
    package_dir={'': 'src'},
    packages=['qdflaskauth'],
    include_package_data=True,
    package_data={
        'qdflaskauth': [
            'templates/qdflaskauth/*.html',
            'qd_conf.toml',
        ],
    },
    install_requires=[
        "Flask>=2.0.0",
        "Flask-Login>=0.5.0",
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
