from enum import Enum
from datetime import datetime
import click_log
from cached_property import cached_property

__all__ = ['School', 'Building', 'User', 'Group', 'Course', 'Section',
           'GradingPeriod', 'Role', 'MessageThread', 'Collection',
           'Enrollment', 'Assignment']

log = click_log.basic_config('lms')


class IdCached(type):
    def __init__(cls, *args, **kwargs):
        """Initialize class properties for caching"""
        cls._cache = {}
        super().__init__(*args, **kwargs)

    def __call__(cls, id_or_data=None, *args, **kwargs):
        if isinstance(id_or_data, dict):
            id = id_or_data['id']
        else:
            id = id_or_data

        try:
            obj = cls._cache[id]
        except KeyError:
            obj = cls._cache[id] = super().__call__(id_or_data, *args, **kwargs)
        return obj


class RestObject(metaclass=IdCached):
    def __init__(self, id_or_data, sc, realm=None):
        """Initialize a new local object with the given properties"""
        self.realm = realm
        self._sc = sc
        if isinstance(id_or_data, dict):
            self._json = id_or_data.copy()
        else:
            self._json = sc.api._get(self.build_rest_path(id_or_data, realm=realm))
        log.debug(f"created {self!r}")

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

    def resync(self):
        """Re-synchronize data from Schoology"""
        sc = self._sc
        path = self.rest_path()
        self.__dict__.clear()
        self.__init__(sc, sc.api._get(path))

    @classmethod
    def build_rest_path(cls, ident, realm=None):
        base = realm.rest_path() if realm is not None else ''
        return base + cls.REST_QUERY.format(id=ident)

    def rest_path(self):
        return self.build_rest_path(self.id(), realm=self.realm)

    def id(self):
        return int(self['id'])

    @classmethod
    def for_id(cls, sc, ident, realm=None):
        """Get an object by its "id" property"""
        return cls(ident, sc, realm=realm)


class School(RestObject):
    """Most basic grouping of courses, groups, and users"""
    REST_QUERY = '/schools/{id}'

    @cached_property
    def buildings(self):
        return [Building(d, self._sc) for d in
                self._sc.api._get(self.rest_path() + '/buildings')]


# Query is not a typo (see Schoology API reference)
class Building(RestObject):
    """Further separation of courses, groups, and users (e.g. campuses)"""
    REST_QUERY = '/schools/{id}'


class User(RestObject):
    """Account corresponding to a user"""
    REST_QUERY = '/users/{id}'

    def __str__(self):
        return self['name_display']

    @property
    def role(self):
        return Role(self['role_id'], self._sc)

    @cached_property
    def sections(self):
        return [Section(d, self._sc) for d in
                self._sc.api._get_depaginate(self.rest_path() + '/sections', 'section')]

    @property
    def courses(self):
        return sorted({s.course for s in self.sections}, key=str)


# XXX resync() not yet tested
class Group(RestObject):
    """Non-academic version of course section; holds members, events, documents, etc."""
    REST_QUERY = '/groups/{id}'

    @cached_property
    def enrollments(self):
        return [Enrollment(d, self._sc, realm=self) for d in
                self._sc.api._get_depaginate(self.rest_path() + '/enrollments', 'enrollment')]


class Course(RestObject):
    """Container for course sections"""
    REST_QUERY = '/courses/{id}'

    @property
    def building(self):
        return Building.for_id(self._sc, self['building_id'])

class Section(RestObject):
    """Section of a parent course in which teachers and students are enrolled"""
    REST_QUERY = '/sections/{id}'

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

    @property
    def grading_periods(self):
        return [GradingPeriod.for_id(self._sc, gp) for gp in
                self['grading_periods']]

    @cached_property
    def enrollments(self):
        return [Enrollment(d, self._sc, realm=self) for d in
                self._sc.api._get_depaginate(self.rest_path() + '/enrollments', 'enrollment')]

    @cached_property
    def assignments(self):
        return [Assignment(gi, self._sc, realm=self) for gi in
                self._sc.api._get(self.rest_path() + '/grade_items')['assignment']]


class GradingPeriod(RestObject):
    """Period during which a course section is active"""
    REST_QUERY = '/gradingperiods/{id}'


class Role(RestObject):
    """Collection of user permissions"""
    REST_QUERY = '/roles/{id}'


# TODO: The real RestObjects here are MessageFolder ("messages/{folder}") and
# MessageThread ("messages/inbox/{id}").  What we get in a MessageFolder is
# analagous to the message headers, and the MessageThread contains the rest of
# the information.
# XXX The above needs to be addressed for these to work with resync()
class Message(RestObject):
    """Private message that can be sent and shared"""
    def __str__(self):
        return self.text

    @property
    def author(self):
        return User.for_id(self._sc, self['author_id'])

    @property
    def recipients(self):
        return [User.for_id(self._sc, uid) for uid in
                self['recipient_ids'].split(',')]

    @cached_property
    def text(self):
        return self['message']


class MessageThread(RestObject):
    """Private message thread that may be multiple messages long"""
    REST_QUERY = '/messages/inbox/{id}'

    def __str__(self):
        return self.subject

    @cached_property
    def subject(self):
        return self['subject']

    @property
    def participants(self):
        return {User.for_id(self._sc, uid) for uid in
                (*self['recipient_ids'].split(','), self['author_id'])}

    @property
    def time(self):
        return datetime.fromtimestamp(self['last_updated']).astimezone()

    @property
    def is_read(self):
        return self['message_status'] == 'read'

    @property
    def messages(self):
        return [Message(m, self._sc) for m in
                self._sc.api._get(f"messages/inbox/{self.id()}")['message']]


class Collection(RestObject):
    """Collections and templates for user and group resources"""
    REST_QUERY = '/collections/{id}'


class Enrollment(RestObject):
    """Association between a user and a course or group"""
    REST_QUERY = '/enrollments/{id}'

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


class Assignment(RestObject):
    """Container for coursework, test, or quiz"""
    REST_QUERY = '/assignments/{id}'

    @cached_property
    def grades(self):
        return [Grade((g['assignment_id'], g['enrollment_id']),
                      g, self._sc, realm=self.realm)
                for g in self._sc.api._get(
                    self.realm.rest_path() + '/grades',
                    params={'assignment_id': self.id()})['grades']['grade']]


# TODO The real RestObject here is Grades, but it can be filtered on
# assignment_id, enrollment_id, or both.
# XXX Does not yet work with resync().  KeyError on assignment_id
class Grade(RestObject):
    """Points assigned to users for a specific assignment"""
    REST_QUERY = '/grades/{id}'

    def id(self):
        return (int(self['assignment_id']), int(self['enrollment_id']))

    @property
    def user(self):
        return Enrollment.for_id(self._sc, self['enrollment_id'],
                realm=self.realm).user

    @property
    def assignment(self):
        return Assignment.for_id(self._sc, self['assignment_id'])
