from enum import Enum
import collections.abc
import click_log
from cached_property import cached_property

__all__ = ['School', 'Building', 'User', 'Group', 'Course', 'Section',
        'GradingPeriod', 'Role', 'Message', 'Collection', 'Enrollment',
        'Assignment']

log = click_log.basic_config('lms')


class RestObject(collections.abc.Hashable):
    def __init_subclass__(cls, rest_query='', **kwargs):
        """Initialize class properties for caching"""
        cls._cache = {}
        cls._rest_query = rest_query
        super().__init_subclass__(**kwargs)

    def __init__(self, sc, json, realm=None):
        """Initialize a new local object with the given properties"""
        self.realm = realm
        self._sc = sc
        self._json = json.copy()
        log.debug(f"caching {self!r}")
        type(self)._cache[self.id()] = self

    def __repr__(self):
        return f"{type(self).__name__}<{self.id()}>"

    def __str__(self):
        return str(self['title'])

    def __getitem__(self, key):
        """Return the property for a given key"""
        return self._json[key]

    def __hash__(self):
        return self.id()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id() == other.id()

    @classmethod
    def build_rest_path(cls, ident, realm=None):
        base = '' if realm is None else realm.rest_path() + '/'
        return base + cls._rest_query.format(id=ident)

    def rest_path(self):
        return self.build_rest_path(self['id'], realm=self.realm)

    def id(self):
        return int(self['id'])

    @classmethod
    def for_id(cls, sc, ident, realm=None):
        """Get an object by its "id" property"""
        ident = int(ident)
        try:
            item = cls._cache[ident]
        except KeyError:
            item = cls(sc, sc.api._get(cls.build_rest_path(ident, realm)))
        return item


class School(RestObject, rest_query='schools/{id}'):
    """Most basic grouping of courses, groups, and users"""

    @cached_property
    def buildings(self):
        return [Building(self._sc, d) for d in
                self._sc.api._get(self.rest_path() + '/buildings')]


# Query is not a typo (see Schoology API reference)
class Building(RestObject, rest_query='schools/{id}'):
    """Further separation of courses, groups, and users (e.g. campuses)"""
    pass


class User(RestObject, rest_query='users/{id}'):
    """Account corresponding to a user"""

    def __str__(self):
        return self['name_display']

    @property
    def role(self):
        return Role.for_id(self._sc, self['role_id'])

    @cached_property
    def sections(self):
        return [Section(self._sc, d) for d in
                self._sc.api._get_depaginate(self.rest_path() + '/sections', 'section')]

    @cached_property
    def courses(self):
        return sorted({s.course for s in self.sections}, key=str)


class Group(RestObject, rest_query='groups/{id}'):
    """Non-academic version of course section; holds members, events,
    documents, etc."""

    @cached_property
    def enrollments(self):
        return [Enrollment(self._sc, d, realm=self) for d in
                self._sc.api._get_depaginate(self.rest_path() + '/enrollments', 'enrollment')]


class Course(RestObject, rest_query='courses/{id}'):
    """Container for course sections"""
    @property
    def building(self):
        return Building.for_id(self._sc, self['building_id'])

class Section(RestObject, rest_query='sections/{id}'):
    """Section of a parent course in which teachers and students are
    enrolled"""

    def __str__(self):
        return f"{self['course_title'].strip()} ({self.grading_periods[0]['title'].strip()})"

    @property
    def school(self):
        return School.for_id(self._sc, self['school_id'])

    @property
    def building(self):
        return Building.for_id(self._sc, self['building_id'])

    @property
    def course(self):
        return Course.for_id(self._sc, self['course_id'])

    @cached_property
    def grading_periods(self):
        return [GradingPeriod.for_id(self._sc, gp) for gp in
                self['grading_periods']]

    @cached_property
    def enrollments(self):
        return [Enrollment(self._sc, d, realm=self) for d in
                self._sc.api._get_depaginate(self.rest_path() + '/enrollments', 'enrollment')]

    @cached_property
    def assignments(self):
        return [Assignment(self._sc, gi, realm=self) for gi in
                self._sc.api._get(self.rest_path() + '/grade_items')['assignment']]


class GradingPeriod(RestObject, rest_query='gradingperiods/{id}'):
    """Period during which a course section is active"""
    pass


class Role(RestObject, rest_query='roles/{id}'):
    """Collection of user permissions"""
    pass


class Message(RestObject, rest_query='messages/inbox/{id}'):
    """Private messages that can be sent and shared"""

    def __str__(self):
        return self['subject']


class Collection(RestObject, rest_query='collections/{id}'):
    """Collections and templates for user and group resources"""
    pass


class Enrollment(RestObject, rest_query='enrollments/{id}'):
    """Association between a user and a course or group"""

    class Status(Enum):
        ACTIVE = 1
        EXPIRED = 2
        INVITED = 3
        REQUESTED = 4
        ARCHIVED = 5

    @property
    def user(self):
        return User.for_id(self._sc, self['uid'])

    @property
    def status(self):
        return Enrollment.Status(int(self['status']))

    @property
    def is_admin(self):
        return bool(int(self['admin']))


class Assignment(RestObject, rest_query='assignments/{id}'):
    """Container for coursework, test, or quiz"""

    @cached_property
    def grades(self):
        return [Grade(self._sc, g, realm=self.realm) for g in
                self._sc.api._get(self.realm.rest_path() + '/grades',
                    params={'assignment_id': self['id']})['grades']['grade']]


class Grade(RestObject, rest_query='grades/{id}'):
    """Points assigned to users for a specific assignment"""

    def id(self):
        return (int(self['assignment_id']), int(self['enrollment_id']))

    @property
    def user(self):
        return Enrollment.for_id(self._sc, self['enrollment_id'],
                realm=self.realm).user

    @property
    def assignment(self):
        return Assignment.for_id(self._sc, self['assignment_id'])
