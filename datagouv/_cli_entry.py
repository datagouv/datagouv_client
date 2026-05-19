import sys


def main():
    try:
        from datagouv.cli import app
    except ImportError:
        print("CLI requires the [cli] extra: pip install datagouv_client[cli]")
        sys.exit(1)
    app()
