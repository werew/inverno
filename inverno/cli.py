import os
from shutil import copyfile
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

@main.command("new-project")
@click.argument("dest")
def new_project(dest: str):
    """
    Generate a template for a new project
    """
    src = os.path.join(os.path.dirname(__file__), "project_template")
    files = ["project.yml", "transactions.csv"]
    for f in files:
        copyfile(os.path.join(src,f), os.path.join(dest,f))
    click.echo("New project created !")
    click.echo("To generate a report run:")
    click.echo("  inverno gen-report project.yml DEST")

    
