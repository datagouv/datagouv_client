import typer

from datagouv import Client
from datagouv.commands.utils import display_json
from datagouv.config import load_config

app = typer.Typer()


@app.command()
def display(id: str) -> None:
    """Display an organization's main attributes in a human-friendly format. `id` required."""
    client = Client(**load_config())
    orga = client.organization(id)
    for att in orga._attributes:
        typer.echo(f"{att}: {getattr(orga, att)}")
        typer.echo("─" * 20)


@app.command()
def get(id: str) -> None:
    """Display all of an organization's attributes in JSON. `id` required."""
    client = Client(**load_config())
    organization = client.organization(id, fetch=False)
    display_json(organization)


@app.command()
def create(
    name: str,
    description: str,
    set: list[str] = typer.Option([], "--set", help="Reusable argument to set extra keys"),
) -> None:
    """Create an organization. `name` and `description` are required.
    Each `--set` option is expected as `<key>=<value>`."""
    client = Client(**load_config())
    payload = {"name": name, "description": description}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value
    o = client.organization().create(payload)
    typer.echo(f"Organization created successfully ✓ id is {o.id}")


@app.command()
def update(
    id: str,
    set: list[str] = typer.Option([], "--set"),
) -> None:
    """Update an organization by `id`. Each `--set` option is expected as `<key>=<new_value>`."""
    client = Client(**load_config())
    payload = {}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value

    client.organization(id, fetch=False).update(payload)
    typer.echo("Organization updated successfully ✓")


@app.command()
def delete(id: str) -> None:
    """Delete an organization by `id`."""
    client = Client(**load_config())
    client.organization(id, fetch=False).delete()
    typer.echo("Organization deleted successfully ✓")
