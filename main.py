from schoology import Schoology
import click
import click_log
from click_repl import repl
import configparser
import xdg

log = click_log.basic_config('lms')

BACKENDS = {
        'schoology': Schoology,
}
CONFIG_FILE = xdg.XDG_CONFIG_HOME/'lms.conf'

conf = configparser.ConfigParser(default_section=None)
conf.read(CONFIG_FILE)

be = BACKENDS[conf['lms']['backend']](conf)
cur_course = None


@click.group(invoke_without_command=True)
@click_log.simple_verbosity_option(log)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        repl(ctx, allow_system_commands=False,
                prompt_kwargs={'completer': None})


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


@cli.command()
@click.argument('search', default='')
def courses(search):
    global cur_course
    for n, c in enumerate(be.me.courses):
        if search.casefold() in str(c).casefold():
            if c is cur_course:
                click.echo(f'*{n:2}. {c}')
            else:
                click.echo(f' {n:2}. {c}')


@cli.command()
@click.argument('num')
def course(num):
    global cur_course
    cur_course = be.me.courses[int(num)]
