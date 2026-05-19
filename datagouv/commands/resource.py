import typer

from datagouv import Client
from datagouv.commands.utils import display_json
from datagouv.config import load_config

app = typer.Typer()


@app.command()
def display(id: str) -> None:
    """Human-friendlily display a resource's attributes."""
    client = Client(**load_config())
    resource = client.resource(id)
    for att in resource._attributes:
        typer.echo(f"{att}: {getattr(resource, att)}")
        typer.echo("─" * 20)


@app.command()
def get(id: str) -> None:
    """Display a resource's metadata in JSON."""
    client = Client(**load_config())
    resource = client.resource(id, fetch=False)
    display_json(resource)


@app.command()
def create(
    dataset_id: str,
    title: str,
    file_to_upload: str = typer.Option(None, help="Path of the file to upload"),
    url: str = typer.Option(None, help="URL of the file"),
    is_communautary: bool = typer.Option(False, help="Whether the resource is communautary"),
    set: list[str] = typer.Option([], "--set", help="Reusable argument to set extra keys"),
) -> None:
    """Create a resource. `dataset-id` and `title` are required.
    Set `file-to-upload` to create a static resource, or `url` to create a remote one.
    Each `--set` option is expected as `<key>=<value>`."""
    assert (file_to_upload or url) and not (file_to_upload and url), (
        "Either `file-to-upload` or `url` should be specified, and not both"
    )
    client = Client(**load_config())
    payload = {"title": title}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value
    if url:
        payload["url"] = url
        r = client.dataset(dataset_id, fetch=False).create_remote(
            payload=payload, is_communautary=is_communautary
        )
    else:
        r = client.dataset(dataset_id, fetch=False).create_static(
            file_to_upload=file_to_upload, payload=payload, is_communautary=is_communautary
        )
    typer.echo(f"Resource created successfully ✓ id is {r.id}")


@app.command()
def update(
    id: str,
    set: list[str] = typer.Option([], "--set"),
) -> None:
    """Update a resource. Each `--set` option is expected as `<key>=<new_value>`."""
    client = Client(**load_config())
    payload = {}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value

    client.resource(id, fetch=False).update(payload)
    typer.echo("Resource updated successfully ✓")


@app.command()
def download(id: str, path: str) -> None:
    """Download a resource to a given path."""
    client = Client(**load_config())
    client.resource(id).download(path)
    typer.echo(f"Resource downloaded successfully at {path} ✓")


@app.command()
def delete(id: str) -> None:
    """Delete a resource."""
    client = Client(**load_config())
    client.resource(id, fetch=False).delete()
    typer.echo("Resource deleted successfully ✓")
