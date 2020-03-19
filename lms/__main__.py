from .schoology import Schoology
import click
from click_repl import repl
import configparser
import xdg

BACKENDS = {
        'schoology': Schoology,
}
CONFIG_FILE = xdg.XDG_CONFIG_HOME/'lms.conf'

conf = configparser.ConfigParser(default_section=None)
conf.read(CONFIG_FILE)

be = BACKENDS[conf['lms']['backend']](conf)
cur_course = None


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        repl(ctx, allow_system_commands=False,
                prompt_kwargs={'completer': None})


@main.command()
def config():
    for s in conf.sections():
        for k, v in conf[s].items():
            click.echo(f'{s}.{k} = {v}')


@main.command()
def schools():
    for school in be.schools:
        click.echo(school)


@main.command()
def me():
    gotta = be.me
    click.echo(gotta)


@main.command()
def langs():
    for code, lang in be.languages.items():
        click.echo(f'{code}\t {lang}')


@main.command()
def sections():
    for sec in be.me.sections:
        click.echo(sec)


@main.command()
@click.argument('search', default='')
def courses(search):
    global cur_course
    for n, c in enumerate(be.me.courses):
        if search.casefold() in str(c).casefold():
            if c is cur_course:
                click.echo(f'*{n:2}. {c}')
            else:
                click.echo(f' {n:2}. {c}')


@main.command()
@click.argument('num')
def course(num):
    global cur_course
    cur_course = be.me.courses[int(num)]

if __name__ == '__main__':
    main()
