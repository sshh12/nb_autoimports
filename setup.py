import setuptools


with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
    name="nb_autoimports",
    version="0.0.3",
    description="Automatically add imports when a notebook raises a NameError.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sshh12/nb_autoimports",
    author="Shrivu Shanakr",
    author_email="shrivu1122@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(),
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)