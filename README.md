![datagouv-client](docs/banner.png)

# **datagouv-client**

[![CircleCI](https://circleci.com/gh/datagouv/datagouv_client.svg?style=svg)](https://circleci.com/gh/datagouv/datagouv_client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python wrapper for the data.gouv.fr API that allows you to interact easily with datasets and resources across all three platforms (production `www`, `demo`, and `dev`). Install it through [PyPI](https://pypi.org/project/datagouv-client/):
```bash
pip install datagouv-client
```

**Requirements:** Python >= 3.10

## 🚀 Use

### 📥 Quick Start
```python
from datagouv import Dataset, Resource, Topic

# Get a dataset and its resources
dataset = Dataset("5d13a8b6634f41070a43dff3")
print(f"Dataset: {dataset.title}")
print(f"Resources: {len(dataset.resources)}")

# Download a resource
resource = dataset.resources[0]
resource.download("my_file.csv")

# Get a topic and its elements
topic = Topic("68b6e6dbdac745f47d4ff6e0")
elements = topic.elements
datasets = topic.datasets
```

### 📊 Getting existing objects
If you only want to retrieve existing objects (aka you don't want to modify them on datagouv), here is what a workflow could look like:
```python
from datagouv import Dataset, Resource, Organization

dataset = Dataset("5d13a8b6634f41070a43dff3")  # you can find a dataset's id in the `Informations` tab of its landing page

# you can now access a bunch of info about the dataset
print(dataset.title)
print(dataset.description)
print(dataset.created_at)
print(dataset.organization)  # this is an instance of Organization
print(dataset)  # this displays all the attributes of the dataset as a dict

# and of course its resources, which are all Resource instances
for res in dataset.resources:
    print(res.title)
    print(res.url)  # this is the download URL of the resource
    print(res.id)  # the id of the resource itself
    print(res.dataset_id)  # the id of the dataset the resource belongs to
    print(res)  # this displays all the attributes of the resource as a dict

# if you are only interested in a specific resource
resource = Resource("f868cca6-8da1-4369-a78d-47463f19a9a3")  # you can find a resource's id in its `Métadonnées` tab
print(resource)

# if the resource contains tabular data that has been APIfied (see https://www.data.gouv.fr/dataservices/673b0e6774a23d9eac2af8ce for more info), it also has:
resource.columns  # the columns of the table, as a list of strings
resource.profile  # the profile of the table (number of rows, detected formats and types...)
for row in resource.rows(
    filters=[
        ("col1", "==", "6"),
        ("col4", "isnotnull"),
    ],  # filters is an optional argument to retrieve only the rows that match the conditions
):
    print(row)

# you can also access a dataset from one of its resources
d = resource.dataset  # this returns an instance of Dataset

# you can also download a resource locally (**Note:** if it doesn't exist, parent path will be created)
resource.download("./file.csv")  # this saves the resource in your working directory as "file.csv"

# and a subset or all resources of a dataset (**Note:** if it doesn't exist, parent path will be created)
# the files are named `resource_id.format` (for instance f868cca6-8da1-4369-a78d-47463f19a9a3.csv)
d.download_resources(
    folder="data",  # if not specified, saves them into your working directory
    resources_types=["main", "documentation"],  # default is only main resources
)


organization = Organization("646b7187b50b2a93b1ae3d45")  # you can find an organization's id in the `Informations` tab of its landing page, in "Informations techniques"
# you can loop through the organization's datasets, which are Dataset instances
for dat in organization.datasets:
    print(f"{dat.title} has {len(dat.resources)} resources")
```

> **Note:** If you encounter errors during API calls, the client will raise appropriate exceptions (e.g., `PermissionError` for authentication issues, `httpx.HTTPError` for API errors).

> **Note:** If you want to get objects from demo or dev, you must use a client:
```python
from datagouv import Client, Dataset, Resource

dataset = Dataset("5d13a8b6634f41070a43dff3", _client=Client("demo"))
```

You can also access objects' metrics (views, downloads) with the `get_monthly_traffic_metrics` function:
```python
for month_metrics in Dataset("5d13a8b6634f41070a43dff3").get_monthly_traffic_metrics(
    start_month="2025-01",  # optional, goes back as far as possible if not set
    end_month="2025-06",  # optional, until today if not set
):
    print(month_metrics)
```
The metrics differ depending on the object:
- for datasets:
```json
{
    "__id": 43110395,
    "dataset_id": "6789251f3a805425afee55e6",
    "metric_month": "2025-01",
    "monthly_visit": 233,
    "monthly_download_resource": 3
}
```
- for resources:
```json
{
    "__id": 58728461,
    "resource_id": "5ffa8553-0e8f-4622-add9-5c0b593ca1f8",
    "dataset_id": "5c4ae55a634f4117716d5656",
    "metric_month": "2025-04",
    "monthly_download_resource": 5669
}
```
- for organizations:
```json
{
    "__id": 7,
    "organization_id": "646b7187b50b2a93b1ae3d45",
    "metric_month": "2023-07",
    "monthly_visit_dataset": 27196,
    "monthly_download_resource": 1085933,
    "monthly_visit_reuse": 123,
    "monthly_visit_dataservice": 456
}
```

### 🛠️ Interacting with objects online
If you want to modify objects on the datagouv platforms, you will need to create an authenticated client:
```python
from datagouv import Client

client = Client(
    environment="www",  # here you can set which platform the client will interact with, default is production
    api_key="MY_SECRET_API_KEY",  # your API key, that grants your rights on the platform
)
```
> **Note:** You can find your API key on https://www.data.gouv.fr/fr/admin/me/ (don't forget to change the prefix to get the key from the right environment).

Once your client is set up, you can instantiate datasets and resources from it. Of course, **you will only be allowed to modify objects according to your rights** (so objects created by you or an organization you are part of):
```python
dataset = client.dataset("5d13a8b6634f41070a43dff3")
# this is also a Dataset instance, with all the same attributes as above, but since you're authenticated, you have access to new methods

dataset.update({"title": "A brand new title"})  # update the dataset online with the payload you give, and also update the attributes of the object
print(dataset.title)  # -> "A brand new title"
dataset.delete()  # delete the dataset, use with caution!

# you can also modify the extras
dataset.update_extras(payload)
dataset.delete_extras(payload)

# the methods are the same for resources
for idx, res in enumerate(dataset.resources):
    res.update({"title": f"Resource n°{idx + 1}"})
    print(res.title)  # -> "Resource n°X"
    # delete every third resource
    if idx % 3 == 0:
        res.delete()
```

With an authenticated client, you are also allowed to create datasets and resources on the environment you specified:
```python
dataset = client.dataset().create(
    {
        "title": "New dataset",
        "description": "A description is required",
        "organization": "646b7187b50b2a93b1ae3d45",  # the organization that will own the dataset
    },
)  # this creates a dataset with the values you specified, and instantiates a Dataset
dataset.update({"tags": ["environment", "water"]})

# alternatively you can create a dataset from an organization, and it will be attached to it
organization = client.organization("646b7187b50b2a93b1ae3d45")
dataset = organization.create_dataset(
    {
        "title": "New dataset",
        "description": "A description is a required",
    }
)
```
There are two types of resources on datagouv:
- `static`: a file is uploaded directly on the platform
- `remote`: reference the URL of a file that is stored somewhere else on the internet

You have two options to create a resource (of any type):
- from the client itself, by specifying the id of the dataset you want to include it into (you must have the rights on the dataset):
```python
# to create a static resource from a file
resource = client.resource().create_static(
    file_to_upload="path/to/your/file.txt",
    payload={"title": "New static resource"},
    dataset_id="5d13a8b6634f41070a43dff3",
)  # this creates a static resource with the values you specified, and instantiates a Resource

# to create a remote resource from an url
resource = client.resource().create_remote(
    payload={"url": "http://example.com/file.txt", "title": "New remote resource"},
    dataset_id="5d13a8b6634f41070a43dff3",
)  # this creates a remote resource with the values you specified, and instantiates a Resource
```
- from the dataset you want to include it into (you must have the rights on the dataset), in which case you don't have to specify the `dataset_id`:
```python
dataset = client.dataset("5d13a8b6634f41070a43dff3")
# to create a static resource from a file
resource = dataset.create_static(
    file_to_upload="path/to/your/file.txt",
    payload={"title": "New static resource"},
)  # this creates a static resource with the values you specified, and instantiates a Resource

# to create a remote resource from an url
resource = dataset.create_remote(
    payload={"url": "http://example.com/file.txt", "title": "New remote resource"},
)  # this creates a remote resource with the values you specified, and instantiates a Resource

# to update the file of a static resource
resource.update({"title": "New title"}, file_to_upload="path/to/your/new_file.txt")
```
> **Note:** If you are not planning to use an object's attributes, you may prevent the initial API call using `fetch=False`, in order not to unnecessarily ping the API.
```python
dataset = client.dataset("5d13a8b6634f41070a43dff3", fetch=False)
print(dataset.title)  # -> this will fail because the attributes are not set from the initial call
# but you can update the object as usual
dataset.update({"title": "New title"})
print(dataset.title)  # -> "New title"   because the attributes are set from the response
```

### ⚡ Advanced features
Many datagouv endpoints are paginated, which can make it tedious to retrieve all objects. An instance of `Client` has a method to create an iterator from any endpoint that returns paginated data:
```python
for obj in client.get_all_from_api_query(
    "api/1/datasets/?organization=534fff81a3a7292c64a77e5c",  # get all datasets from a specific organization
    mask="data{id,title,resources{id,title}}",  # you can apply a mask to retrieve only specific fields of the objects
    cast_as=Dataset,  # you can get the results as objects to manipulate them more easily
):
    print(f"Dataset {obj['title']} has {len(obj['resources'])} resources")  # if cast_as is not used, otherwise `obj.id` and `obj.resources`
```

You can also check if resources have been updated more recently than others:
```python
# Check if any resource in a dataset has been updated more recently than a specific resource
resource = Resource("f868cca6-8da1-4369-a78d-47463f19a9a3")
has_newer_updates = resource.check_if_more_recent_update("5d13a8b6634f41070a43dff3")
```

## 🤝 Contribution
Contributions and feedback are welcome! Main guidelines:
- as few API calls as possible (use responses to create/update objects)
- build on the existing

Remember to format, lint, and sort imports with [Ruff](https://docs.astral.sh/ruff/) before committing (checks will remind you anyway):
```bash
pip install .[dev]
ruff check --fix .
ruff format .
```

### 🏷️ Release

The release process uses the [`tag_version.sh`](tag_version.sh) script to create git tags and update [CHANGELOG.md](CHANGELOG.md) and [pyproject.toml](pyproject.toml) automatically.

**Prerequisites**: [GitHub CLI](https://cli.github.com/) (`gh`) must be installed and authenticated, and you must be on the main branch with a clean working directory.

```bash
# Create a new release
./tag_version.sh <version>

# Example
./tag_version.sh 2.5.0

# Dry run to see what would happen
./tag_version.sh 2.5.0 --dry-run
```

The script automatically:
- Updates the version in `pyproject.toml`
- Extracts commits since the last tag and formats them for `CHANGELOG.md`
- Identifies breaking changes (commits with `!:` in the subject)
- Creates a git tag and pushes it to the remote repository
- Creates a GitHub release with the changelog content
