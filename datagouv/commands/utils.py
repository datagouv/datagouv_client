import typer

from datagouv.utils.base_object import BaseObject


def display_json(obj: BaseObject) -> None:
    r = obj._client.session.get(obj.uri)
    try:
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(r.text) from e
    typer.echo(r.text)
