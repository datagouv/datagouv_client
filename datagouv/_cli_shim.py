import sys

_MESSAGE = """
The datagouv CLI has moved to datagouv-cli.

Install it via:
  - apt: see https://github.com/datagouv/datagouv-cli#manual-apt-debian--ubuntu
  - brew: brew install datagouv/tap/datagouv-cli
  - binary: https://github.com/datagouv/datagouv-cli/releases
"""


def main() -> None:
    print(_MESSAGE.strip(), file=sys.stderr)
    raise SystemExit(1)
