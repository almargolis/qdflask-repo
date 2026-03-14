"""
Setup script for qdflaskapi package.
"""

from setuptools import setup

setup(
    name="qdflaskapi",
    version="0.1.0",
    author="Albert Margolis",
    author_email="almargolis@gmail.com",
    description="API key authentication and management for QuickDev Flask apps",
    long_description="API key authentication middleware and key management routes for Flask.",
    long_description_content_type="text/plain",
    url="https://github.com/almargolis/quickdev",
    project_urls={
        "Bug Tracker": "https://github.com/almargolis/quickdev/issues",
        "Source Code": "https://github.com/almargolis/quickdev/tree/master/qdflaskapi",
    },
    license="MIT",
    package_dir={'': 'src'},
    packages=['qdflaskapi'],
    include_package_data=True,
    package_data={
        'qdflaskapi': ['qd_conf.toml'],
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
