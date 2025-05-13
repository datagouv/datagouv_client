# **datagouv_client**
This package is a python wrapper for the data.gouv.fr API. It allows you to interact easily with datasets and resources, on all three platforms (production aka `www`, `demo` and `dev`). You can install it through `pypi`:
```bash
pip install datagouv-client
```
in an environment that runs on `python>=3.10`.

## Use

### Getting existing datasets and resources
If you only want to retrieve existing objects (aka you don't want to modify them on datagouv), here is what a workflow could look like:
```python
from datagouv import Dataset, Resource

dataset = Dataset("5d13a8b6634f41070a43dff3")  # you can find a dataset's id in the `Informations` tab of its landing page

# you can now access a bunch of info of the dataset
print(dataset.title)
print(dataset.description)
print(dataset.created_at)
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

# you can also access a dataset from one of its resources
d = resource.dataset()  # NB: this is a method, and returns an instance of Dataset

# you can also download a resource locally (NB: make sure to create the parent folders upstream)
resource.download("./file.csv")  # this saves the resource in your working directory as "file.csv"

# and a subset or all resources of a dataset (NB: make sure to create the parent folders upstream)
# the files are named `resource_id.format` (for instance f868cca6-8da1-4369-a78d-47463f19a9a3.csv)
d.download_resources(
    folder="data",  # if not specified, saves them into your working directory
    resources_types=["main", "documentation"],  # default is only main resources
)
```

### Interacting with objects online
If you want to modify objects on the datagouv platforms, you will need to create an authenticated client:
```python
from datagouv import Client

client = Client(
    environment="www",  # here you can set which platform the client will interact with, default is production
    api_key="MY_SECRET_API_KEY",  # your API key, that grants your rights on the platform
)
```
> NB: you can find your API key on https://www.data.gouv.fr/fr/admin/me/ (don't forget to change the prefix to get the key from the right environment).

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
        "description": "A description is a required",
        "organization": "646b7187b50b2a93b1ae3d45",  # the organization that will own the dataset
    },
)  # this creates a dataset with the values you specified, and instantiates a Dataset
dataset.update({"tags": ["environment", "water"]})
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
> NB: If you are not planning to use an object's attributes, you may prevent the initial API call using `fetch=False`, in order not to unnecessarily ping the API.
```python
dataset = client.dataset("5d13a8b6634f41070a43dff3", fetch=False)
print(dataset.title)  # -> this will fail because the attributes are not set from the initial call
# but you can update the object as usual
dataset.update({"title": "New title"})
print(dataset.title)  # -> "New title"   because the attributes are set from the response
```

### Advanced features
Many datagouv endpoints are paginated, which can make it tedious to retrieve all objects. An instance of `Client` has a method to create an iterator from any endpoint that returns paginated data:
```python
for obj in client.get_all_from_api_query(
    "api/1/datasets/?organization=534fff81a3a7292c64a77e5c",  # get all datasets from a specific organization
    mask="data{id,title,resources{id,title}}",  # you can apply a mask to retrieve only specific fields of the objects
):
    print(f"Dataset {obj['title']} has {len(obj['resources'])} resources")
```

## Contribution
Contributions and feedback are welcome! Main guidelines:
- as few API calls as possible (use responses to create/update objects)
- build on the existing

Remember to format, lint, and sort imports with [Ruff](https://docs.astral.sh/ruff/) before committing (checks will remind you anyway):
```bash
ruff check --fix .
ruff format .
```

## Release
The release process uses [bump'X](https://github.com/datagouv/bumpx).
