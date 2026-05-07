import typer

from datagouv import Client
from datagouv.config import load_config

app = typer.Typer()


@app.command()
def display(id: str) -> None:
    """Display a topic."""
    client = Client(**load_config())
    topic = client.topic(id)
    for att in topic._attributes:
        typer.echo(f"{att}: {getattr(topic, att)}")
        typer.echo("─" * 20)


@app.command()
def create(
    name: str,
    organization_id: str = typer.Option(
        None, help="Id of the organization that will own the topic"
    ),
    owner_id: str = typer.Option(None, help="Id of the user that will own the topic"),
    set: list[str] = typer.Option([], "--set", help="Reusable argument to set extra keys"),
) -> None:
    """Create a topic. `name` and `description` are required.
    Each `--set` option is expected as `<key>=<new_value>`."""
    assert (organization_id or owner_id) and not (organization_id and owner_id), (
        "Either `organization-id` or `owner-id` should be specified, and not both"
    )
    client = Client(**load_config())
    payload = {"name": name}
    if organization_id:
        payload["organization"] = organization_id
    else:
        payload["owner"] = owner_id
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value
    t = client.topic().create(payload)
    typer.echo(f"Topic created successfully ✓ id is : {t.id}")


@app.command()
def update(
    id: str,
    set: list[str] = typer.Option([], "--set"),
) -> None:
    """Update a topic. Each `--set` option is expected as `<key>=<new_value>`."""
    client = Client(**load_config())
    payload = {}
    for item in set:
        key, value = item.split("=", maxsplit=1)
        payload[key] = value

    client.topic(id, fetch=False).update(payload)
    typer.echo("Topic updated successfully ✓")


@app.command()
def delete(id: str) -> None:
    """Delete a topic."""
    client = Client(**load_config())
    client.topic(id, fetch=False).delete()
    typer.echo("Topic deleted successfully ✓")
