import schoolopy
from cached_property import cached_property


class Schoology:
    def __init__(self, config):
        self.conf = dict(config)
        self.sc = schoolopy.Schoology(schoolopy.Auth(self.conf['key'], self.conf['secret']))

    def _get(self, *args, **kwargs):
        return self.sc._get(*args, **kwargs)

    @cached_property
    def schools(self):
        return [School(self.sc, d) for d in self._get('schools')['school']]

    @cached_property
    def me(self):
        return User(self.sc, self._get('users/me'))

    @cached_property
    def languages(self):
        return {l['language_code']: l['language_name'] for l in self._get('users/languages')['language']}


class User:
    def __init__(self, sc, props):
        self.sc = sc
        self.__dict__.update(props)


class School:
    def __init__(self, sc, props):
        self.sc = sc
        self.__dict__.update(props)

    @cached_property
    def buildings(self):
        return [Building(self.sc, d) for d in self.sc._get('schools/' + self.id + '/buildings')]


class Building:
    def __init__(self, sc, props):
        self.sc = sc
        self.__dict__.update(props)
