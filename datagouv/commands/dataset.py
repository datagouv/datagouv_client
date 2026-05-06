import typer

from datagouv import Client, Dataset
from datagouv.config import load_config

app = typer.Typer()


@app.command()
def display(id: str) -> None:
    """Display a dataset."""    
    dataset = Dataset(id)
    for att in dataset._attributes:
        typer.echo(f"{att}: {getattr(dataset, att)}")
        typer.echo("_" * 20)


@app.command()
def create(
    title: str,
    description: str,
    organization: str = typer.Option(None, help="Id of the organization that will own the dataset"),
    owner: str = typer.Option(None, help="Id of the user that will own the dataset"),
    set: list[str] = typer.Option([], "--set", help="Reusable argument to set extra keys"),
) -> None:
    """Create a dataset. `title` and `description` are required.
    Each `--set` option is expected as `<key>=<new_value>`."""
    assert (organization or owner) and not (organization and owner), "Either `organization` or `owner` should be specified"
    client = Client(**load_config())
    payload = {"title": title, "description": description}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value
    if organization:
        client.organization(organization, fetch=False).create_dataset(payload)
    else:
        client.dataset().create(payload | {"owner": owner})
    typer.echo("Dataset created successfully ✓")


@app.command()
def update(
    id: str,
    set: list[str] = typer.Option([], "--set"),
) -> None:
    """Update a dataset. Each `--set` option is expected as `<key>=<new_value>`."""
    client = Client(**load_config())
    payload = {}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value
    
    client.dataset(id, fetch=False).update(payload)
    typer.echo("Dataset updated successfully ✓")


@app.command()
def delete(id: str) -> None:
    """Delete a dataset."""
    client = Client(**load_config())
    client.dataset(id, fetch=False).delete()
    typer.echo("Dataset deleted successfully ✓")
