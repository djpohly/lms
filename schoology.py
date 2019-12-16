import schoolopy
from cached_property import cached_property


class Schoology:
    def __init__(self, config):
        self.conf = config['schoology']
        auth = schoolopy.Auth(self.conf['key'], self.conf['secret'])
        self.sc = schoolopy.Schoology(auth)
        self._get = self.sc._get
        self.objs = {}

    def get(self, cls, ident):
        try:
            item = self.objs[cls, ident]
        except KeyError:
            item = cls(self, ident)
            self.objs[cls, ident] = item
        return item

    @cached_property
    def me(self):
        return User(self, self._get('users/me'))

    @cached_property
    def languages(self):
        return {l['language_code']: l['language_name'] for l in
                self._get('users/languages')['language']}

    @cached_property
    def schools(self):
        return [School(self, d) for d in
                self._get('schools')['school']]

    @cached_property
    def collections(self):
        return [Collection(self, d) for d in
                self._get('collections')['collection']]


class RestObject:
    def __init_subclass__(cls, rest_query='', **kwargs):
        """Initialize class properties for caching"""
        cls._cache = {}
        cls._rest_query = rest_query
        super().__init_subclass__(**kwargs)

    def __init__(self, sc, props):
        """Initialize a new local object with the given properties"""
        self._sc = sc
        self._prop = props.copy()
        type(self)._cache[str(self['id'])] = self

    def __repr__(self):
        return f"{type(self).__name__}<{self['id']}>"

    def __str__(self):
        return str(self['title'])

    def __lt__(self, other):
        return self['title'] < other['title']

    def __getitem__(self, key):
        """Return the property for a given key"""
        return self._prop[key]

    def keys(self):
        """Return the keys available for this object"""
        return self._prop.keys()

    @classmethod
    def get(cls, sc, ident):
        """Get an object by its "id" property"""
        ident = str(ident)
        try:
            item = cls._cache[ident]
        except KeyError:
            item = cls(sc, sc._get(cls._rest_query.format(ident)))
        return item


class School(RestObject, rest_query='schools/{}'):
    """Most basic grouping of courses, groups, and users"""

    @cached_property
    def buildings(self):
        return [Building(self._sc, d) for d in
                self._sc._get(f"schools/{self['id']}/buildings")]


# Query is not a typo (see Schoology API reference)
class Building(RestObject, rest_query='schools/{}'):
    """Further separation of courses, groups, and users (e.g. campuses)"""
    pass


class User(RestObject, rest_query='users/{}'):
    """Account corresponding to a user"""

    def __str__(self):
        return self['name_display']

    @property
    def role(self):
        return Role.get(self._sc, self['role_id'])

    @cached_property
    def sections(self):
        return [Section(self._sc, d) for d in
                self._sc._get(f"users/{self['id']}/sections")['section']]

    @cached_property
    def courses(self):
        return sorted({s.course for s in self.sections})


class Group(RestObject, rest_query='groups/{}'):
    """Non-academic version of course section; holds members, events,
    documents, etc."""
    pass


class Course(RestObject, rest_query='courses/{}'):
    """Container for course sections"""
    pass

class Section(RestObject, rest_query='sections/{}'):
    """Section of a parent course in which teachers and students are
    enrolled"""

    def __str__(self):
        return f"{self['course_title'].strip()} ({self.grading_periods[0]['title'].strip()})"

    @property
    def school(self):
        return School.get(self._sc, self['school_id'])

    @property
    def building(self):
        return Building.get(self._sc, self['building_id'])

    @property
    def course(self):
        return Course.get(self._sc, self['course_id'])

    @cached_property
    def grading_periods(self):
        return [GradingPeriod.get(self._sc, gp) for gp in
                self['grading_periods']]


class GradingPeriod(RestObject, rest_query='gradingperiods/{}'):
    """Period during which a course section is active"""
    pass


class Role(RestObject, rest_query='roles/{}'):
    """Collection of user permissions"""
    pass


class Message(RestObject, rest_query='messages/inbox/{}'):
    """Private messages that can be sent and shared"""

    def __str__(self):
        return self['id']


class Collection(RestObject, rest_query='collections/{}'):
    """Collections and templates for user and group resources"""
    pass
