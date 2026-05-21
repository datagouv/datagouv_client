import typer

from datagouv import Client
from datagouv.commands.utils import display_json
from datagouv.config import load_config

app = typer.Typer()


@app.command()
def display(id: str) -> None:
    """Display the main attributes of a dataset in a human-friendly format. `id` required."""
    client = Client(**load_config())
    dataset = client.dataset(id)
    for att in dataset._attributes:
        typer.echo(f"{att}: {getattr(dataset, att)}")
        typer.echo("─" * 20)


@app.command()
def get(id: str) -> None:
    """Display all attributes of a dataset in JSON (title, description, resources, ...). `id` required."""
    client = Client(**load_config())
    dataset = client.dataset(id, fetch=False)
    display_json(dataset)


@app.command()
def create(
    title: str,
    description: str,
    organization_id: str = typer.Option(
        None, help="Id of the organization that will own the dataset"
    ),
    owner_id: str = typer.Option(None, help="Id of the user that will own the dataset"),
    set: list[str] = typer.Option([], "--set", help="Reusable argument to set extra keys"),
) -> None:
    """Create a dataset. `title` and `description` are required.
    Set `organization-id` or `owner-id` to attach the dataset to the desired entity.
    Each `--set` option is expected as `<key>=<value>`."""
    assert (organization_id or owner_id) and not (organization_id and owner_id), (
        "Either `organization-id` or `owner-id` should be specified, and not both"
    )
    client = Client(**load_config())
    payload = {"title": title, "description": description}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value
    if organization_id:
        d = client.organization(organization_id, fetch=False).create_dataset(payload)
    else:
        d = client.dataset().create(payload | {"owner": owner_id})
    typer.echo(f"Dataset created successfully ✓ id is {d.id}")


@app.command()
def update(
    id: str,
    set: list[str] = typer.Option([], "--set"),
) -> None:
    """Update a dataset by `id`. Each `--set` option is expected as `<key>=<new_value>`."""
    client = Client(**load_config())
    payload = {}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value

    client.dataset(id, fetch=False).update(payload)
    typer.echo("Dataset updated successfully ✓")


@app.command()
def sort_resources(
    id: str,
    by: str,
) -> None:
    """Sort the resources of a dataset according to the given order, expected as `<key>.<asc/desc>`.
    Example: `title.asc`"""
    client = Client(**load_config())
    client.dataset(id, fetch=False).sort_resources(by=by)
    typer.echo("Dataset's resources reordered successfully ✓")


@app.command()
def delete(id: str) -> None:
    """Delete a dataset by `id`."""
    client = Client(**load_config())
    client.dataset(id, fetch=False).delete()
    typer.echo("Dataset deleted successfully ✓")
