from pathlib import Path

from setuptools import find_packages, setup


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

with open(this_directory / "datagouv/__init__.py") as f:
    lines = f.readlines()
    for line in lines:
        if line.startswith("__version__"):
            _, _, version = line.replace("'", "").replace('"', "").split()
            break


def pip(filename):
    """Parse pip reqs file and transform it to setuptools requirements."""
    return open(filename).readlines()


setup(
    name="datagouv_client",
    version=version,
    author="Etalab",
    author_email="opendatateam@data.gouv.fr",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    description="Wrapper for the data.gouv.fr API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="api wrapper datagouv",
    license="https://spdx.org/licenses/MIT.html#licenseText",
    url="https://www.data.gouv.fr",
    project_urls={
        "Documentation": "https://www.data.gouv.fr/fr/dataservices/api-catalogue-des-donnees-ouvertes-data-gouv-fr/",
        "Source": "https://github.com/datagouv/datagouv_client",
    },
    data_files=[
        ("share/datagouv_client", ["CHANGELOG.md", "LICENSE", "README.md"]),
    ],
    entry_points={
        "console_scripts": [
            "datagouv_client=datagouv_client.cli:run",
        ],
    },
    setup_requires=pip("requirements-build.txt"),
    install_requires=pip("requirements.txt"),
    extras_require={
        "dev": pip("requirements-dev.txt"),
    },
    packages=find_packages(),
)
