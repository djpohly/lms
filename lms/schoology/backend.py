from .api import SchoologyApi
from .objects import *
import click_log
from cached_property import cached_property

log = click_log.basic_config('lms')


class Schoology:
    def __init__(self, config):
        self.conf = config['schoology']
        self.api = SchoologyApi(self.conf['key'], self.conf['secret'])
        self.objs = {}

    def get(self, cls, ident):
        ident = int(ident)
        try:
            item = self.objs[cls, ident]
        except KeyError:
            item = cls(self, ident)
            self.objs[cls, ident] = item
        return item

    @cached_property
    def me(self):
        return User(self, self.api._get('users/me'))

    @cached_property
    def languages(self):
        return {l['language_code']: l['language_name'] for l in
                self.api._get('users/languages')['language']}

    @cached_property
    def schools(self):
        return [School(self, d) for d in
                self.api._get('schools')['school']]

    @cached_property
    def collections(self):
        return [Collection(self, d) for d in
                self.api._get_depaginate('collections', 'collection')]
