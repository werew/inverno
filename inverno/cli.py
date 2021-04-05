import click
from .project import Project

@click.group()
def main():
    pass

@main.command("make_report")
@click.argument("config")
def make_report(config: str):
    proj = Project(config=config)