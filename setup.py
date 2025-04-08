#! /usr/bin/env python3

from setuptools import find_packages, setup


def pip(filename):
    """Parse pip reqs file and transform it to setuptools requirements."""
    return open(filename).readlines()


setup(
    name="datagouv_client",
    version=__import__("datagouv").__version__,
    author="Etalab",
    author_email="opendatateam@data.gouv.fr",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    description="Detect CSV column content",
    long_description_content_type="text/markdown",
    keywords="CSV data processing encoding guess parser tabular",
    license="http://www.fsf.org/licensing/licenses/agpl-3.0.html",
    url="https://github.com/datagouv/datagouv_client",
    data_files=[
        ("share/datagouv_client", ["CHANGELOG.md", "LICENSE.AGPL.txt", "README.md"]),
    ],
    entry_points={
        "console_scripts": [
            "datagouv_client=datagouv_client.cli:run",
        ],
    },
    include_package_data=True,  # Will read MANIFEST.in
    install_requires=pip("requirements.txt"),
    packages=find_packages(),
)
