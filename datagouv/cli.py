import typer

from datagouv import Client
from datagouv.commands import dataset, organization, resource, topic
from datagouv.config import CONFIG_PATH, _delete_config, save_config

app = typer.Typer()

app.add_typer(dataset.app, name="dataset")
app.add_typer(organization.app, name="organization")
app.add_typer(resource.app, name="resource")
app.add_typer(topic.app, name="topic")


@app.command()
def setup(
    environment: str = typer.Option(
        "prod",
        prompt="The environment you intend to interact with",
        help="Which environment to target (prod/www, demo or dev).",
    ),
    api_key: str | None = typer.Option(
        "",
        prompt="Your API key (or leave blank to remain anonymous)",
        hide_input=True,
        help="Your API key for the specified environment. You may leave it blank if you only intend to get data.",
    ),
):
    """Store configuration (environment and API key)."""
    if CONFIG_PATH.exists():
        typer.echo("A config file already exists, it will be overwritten")
    Client._env_sanity(environment)
    save_config(environment, api_key)
    typer.echo("Config saved ✓")


@app.command()
def delete_config():
    """Delete configuration."""
    _delete_config()
    typer.echo("Config deleted ✓")


if __name__ == "__main__":
    app()
