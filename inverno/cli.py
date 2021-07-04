import click
from .project import Project

@click.group()
def main():
    pass

@main.command("gen-report")
@click.argument("config")
@click.argument("dest")
def make_report(config: str, dest: str):
    """
    Generate an html report from a config
    """
    proj = Project(config=config)
    proj.gen_report(dest)
