import os
from setuptools import setup


def get_readme():
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="nb_autoimports",
    version="0.0.1",
    description="Automatically add imports when a notebook raises a NameError.",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/sshh12/nb_autoimports",
    author="Shrivu Shanakr",
    author_email="shrivu1122@gmail.com",
    license="MIT",
    py_modules=["nb_autoimports"],
    zip_safe=False,
    install_requires=[],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)