import click

from . import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main() -> None:
    """Carpool command-line interface.

    Use subcommands to interact with the application.
    """
    pass


@main.command()
@click.option("--name", "name", default="world", show_default=True, help="Name to greet")
def hello(name: str) -> None:
    """Say hello to someone."""
    click.echo(f"Hello, {name}!")


@main.command()
def version() -> None:
    """Show the package version."""
    click.echo(__version__)
