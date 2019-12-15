from schoology import *
import click
from click_repl import repl
import configparser
import xdg
import sys

CONFIG_FILE = xdg.XDG_CONFIG_HOME/'lms.conf'
conf = configparser.ConfigParser(default_section=None)
conf.read(CONFIG_FILE)
be = Schoology(conf['schoology'])

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        repl(ctx, allow_system_commands=False, prompt_kwargs={'completer': None})

@cli.command()
def config():
    for s in conf.sections():
        for k, v in conf[s].items():
            click.echo(f'{s}.{k} = {v}')

@cli.command()
def schools():
    for school in be.schools:
        click.echo(school)

@cli.command()
def me():
    gotta = be.me
    click.echo(gotta)

@cli.command()
def langs():
    for code, lang in be.languages.items():
        click.echo(f'{code}\t {lang}')

@cli.command()
def sections():
    for sec in be.me.sections:
        click.echo(sec)
