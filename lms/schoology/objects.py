from .util import *
from .enums import *
from datetime import datetime


# RestObject classes which set _REALM_TYPE will self-register here
REALMS = {}


def LazyProperty(name, *fns):
    def _get(self):
        # XXX If the property isn't there, this will attempt reload every time
        # Perhaps track in RestObject whether fully loaded and don't attempt again.
        if name not in self._data:
            self.reload()
        value = self._data.get(name)
        if value is not None:
            # TODO: pass "self" somewhere in here for access to e.g. realm?
            for fn in fns:
                value = fn(value)
        return value
    return property(_get)


# TODO: re-add object caching by ID (or rest_path)
class RestObject:
    API = None

    # Defaults
    _REST_PATH = '/{_REALM_TYPE}s/{id}'
    _PROPERTIES = {}

    @classmethod
    def set_api(cls, api):
        cls.API = api

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls, '_REALM_TYPE', None):
            REALMS[cls._REALM_TYPE] = cls
        for name, ctor in cls._PROPERTIES.items():
            setattr(cls, name, LazyProperty(name, ctor))

    def __init__(self, id_or_data, *args, realm=None, **kwargs):
        super().__init__(*args, **kwargs)
        if realm is not None:
            self.realm_type = realm._REALM_TYPE
            self.realm_id = realm.id
        if isinstance(id_or_data, dict):
            self._data = id_or_data.copy()
        else:
            self._data = dict(id=id_or_data)

    def __getitem__(self, name):
        return getattr(self, name)

    def __str__(self):
        return str(self['title'])

    def rest_path(self):
        if not self._REST_PATH:
            return None
        return self._REST_PATH.format_map(self)

    def reload(self):
        path = self.rest_path()
        if path:
            self._data.update(self.API._get(path))


class School(RestObject):
    """Most basic grouping of courses, groups, and users"""

    _REALM_TYPE = 'school'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'address1': str,
                   'address2': str,
                   'city': str,
                   'state': str,
                   'postal_code': str,
                   'country': str,
                   'website': str,
                   'phone': str,
                   'fax': str,
                   'picture_url': str}

    @property
    def buildings(self):
        return [Building(d) for d in
                self.API._get(self.rest_path() + '/buildings')]


class Building(RestObject):
    """Further separation of courses, groups, and users (e.g. campuses)"""

    # Not a typo
    _REALM_TYPE = 'school'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'address1': str,
                   'address2': str,
                   'city': str,
                   'state': str,
                   'postal_code': str,
                   'country': str,
                   'website': str,
                   'phone': str,
                   'fax': str,
                   'building_code': str,
                   'picture_url': str}


class Role(RestObject):
    _REALM_TYPE = 'role'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'faculty': bool,
                   'role_type': RoleType}


class Group(RestObject):
    """
    Non-academic version of course section; holds members, events, documents,
    etc.
    """

    _REALM_TYPE = 'group'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'description': str,
                   'website': str,
                   'access_code': str,
                   # 'category': GroupCategory,
                   'options': GroupOptions.from_dict,
                   'group_code': str,
                   'privacy_level': PrivacyLevel.__getattr__,
                   'picture_url': str,
                   'admin': bool}

    school = LazyProperty('school_id', int, School)
    building = LazyProperty('building_id', int, Building)

    @property
    def enrollments(self):
        return [Enrollment(d, realm=self) for d in
                self.API._get_depaginate(self.rest_path() + '/enrollments', 'enrollment')]


# TODO: investigate requesting with ?extended=TRUE
class User(RestObject):
    """Account corresponding to a user"""

    _REALM_TYPE = 'user'
    _PROPERTIES = {'id': int,
                   'synced': bool,
                   'school_uid': str,
                   'additional_buildings': csv_to_list(Building),
                   'name_title': str,
                   'name_title_show': bool,
                   'name_first': str,
                   'name_first_preferred': str,
                   'name_middle': str,
                   'name_middle_show': bool,
                   'name_last': str,
                   'name_display': str,
                   'username': str,
                   'primary_email': str,
                   'picture_url': str,
                   'gender': Gender.__getattr__,
                   'position': str,
                   'grad_year': int,
                   'password': str,
                   'tz_offset': int,
                   'tz_name': str,
                   'child_uids': csv_to_list(int, 'User'),
                   'send_message': bool,
                   'language': str,  # Undocumented
                   'permissions': UserPermissions.from_dict}

    school = LazyProperty('school_id', int, School)
    building = LazyProperty('building_id', int, Building)
    role = LazyProperty('role_id', int, Role)
    # Undocumented:
    use_preferred_first_name = LazyProperty('use_preferred_first_name',
                                            int, bool)

    def __str__(self):
        return self.name_display

    @property
    def groups(self):
        return [Group(d) for d in
                self.API._get_depaginate(self.rest_path() + '/groups', 'group')]

    @property
    def sections(self):
        return [Section(d) for d in
                self.API._get_depaginate(self.rest_path() + '/sections', 'section')]


class GradingPeriod(RestObject):
    _REALM_TYPE = 'gradingperiod'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'start': parsedate,
                   'end': parsedate,
                   'active': bool,
                   # Undocumented from here down
                   'has_children': bool,
                   'parent': int}


class Course(RestObject):
    _REALM_TYPE = 'course'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'course_code': str,
                   'department': str,
                   'description': str,
                   'credits': int,
                   'subject_area': SubjectArea,
                   'grade_level_range_start': int,
                   'grade_level_range_end': int,
                   'synced': bool}

    building = LazyProperty('building_id', int, Building)


class Section(RestObject):
    _REALM_TYPE = 'section'
    _PROPERTIES = {'id': int,
                   'course_title': str,
                   'course_code': str,
                   'access_code': str,
                   # Replaced with 'title'
                   # 'section_title': str,
                   'section_code': str,
                   'section_school_code': str,
                   'synced': lambda s: bool(int(s)),
                   'active': bool,
                   'description': str,
                   'subject_area': lambda s: SubjectArea(int(s)),  # Not documented under Section
                   'grade_level_range_start': int,
                   'grade_level_range_end': int,
                   'parent_id': int,  # Undocumented
                   'grading_periods': lambda gps: list(map(GradingPeriod, gps)),
                   'profile_url': str,
                   'location': str,
                   'meeting_days': lambda days: list(map(int, filter(bool, days))),
                   'start_time': parsetime,
                   'end_time': parsetime,
                   'weight': str,  # Undocumented, maybe int or float?
                   # TODO deal with this later
                   # 'options': {'weighted_grading_categories': '1',
                   #             'upload_documents': '0',
                   #             'create_discussion': '0',
                   #             'member_post': '1',
                   #             'member_post_comment': '1',
                   #             'default_grading_scale_id': 0,
                   #             'content_index_visibility': {'topics': 0,
                   #                                          'assignments': 0,
                   #                                          'assessments': 0,
                   #                                          'course_assessment': 0,
                   #                                          'common_assessments': 0,
                   #                                          'documents': 0,
                   #                                          'discussion': 0,
                   #                                          'album': 0,
                   #                                          'pages': 0},
                   #             'hide_overall_grade': 0,
                   #             'hide_grading_period_grade': 0,
                   #             'allow_custom_overall_grade': 0,
                   #             'allow_custom_overall_grade_text': 0},
                   'admin': bool}

    course = LazyProperty('course_id', int, Course)
    school = LazyProperty('school_id', int, School)
    building = LazyProperty('building_id', int, Building)
    title = LazyProperty('section_title', str)

    def __str__(self):
        return f"{self.course_title.strip()} ({self.grading_periods[0].title.strip()})"

    @property
    def enrollments(self):
        return [Enrollment(d, realm=self) for d in
                self.API._get_depaginate(self.rest_path() + '/enrollments', 'enrollment')]

    @property
    def assignments(self):
        return [Assignment(d, realm=self) for d in
                self.API._get(self.rest_path() + '/grade_items')['assignment']]


class Enrollment(RestObject):
    _REST_PATH = '/{realm_type}s/{realm_id}/enrollments/{id}'
    _PROPERTIES = {'id': int,
                   'school_uid': str,
                   'name_title': str,
                   'name_title_show': lambda x: bool(int(x)),
                   'name_first': str,
                   'name_first_preferred': str,
                   'use_preferred_first_name': lambda x: bool(int(x)),
                   'name_middle': str,
                   'name_middle_show': lambda x: bool(int(x)),
                   'name_last': str,
                   'name_display': str,
                   'admin': bool,
                   'status': lambda x: EnrollmentStatus(int(x)),
                   'picture_url': str,
                   # Undocumented, only when realm='section'
                   'enrollment_source': int}

    user = LazyProperty('uid', int, User)


class Collection(RestObject):
    _REALM_TYPE = 'collection'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'shared_users': int,
                   'is_default': DefaultCollections,
                   'realm_id': int,
                   'realm_link': str}

    user = LazyProperty('uid', int, User)
    realm_type = LazyProperty('realm', str)

    @property
    def realm(self):
        if self.realm_id is None:
            return None
        return REALMS[self.realm_type](self.realm_id)


class Assignment(RestObject):
    _REST_PATH = '/{realm_type}s/{realm_id}/grade_items/{id}'
    _PROPERTIES = {'id': int,
                   'title': str,
                   'description': str,
                   'due': parsedatetime,
                   'grading_scale': int,  # TODO: add GradingScale
                   'grading_period': GradingPeriod,
                   'grading_category': int,  # TODO: add GradingCategory
                   'max_points': float,
                   'factor': float,
                   'is_final': lambda x: bool(int(x)),
                   'show_comments': lambda x: bool(int(x)),
                   'grade_stats': lambda x: bool(int(x)),
                   'allow_dropbox': lambda x: bool(int(x)),
                   'allow_discussion': lambda x: bool(int(x)),
                   'published': lambda x: bool(int(x)),
                   'type': GradeItemType.__getitem__,
                   # TODO: consider GradeItem as a supertype?
                   # 'grade_item_id': 2401485639,  // 0 for grade_column, discussion_id for discussion
                   'available': bool,
                   'completed': bool,
                   'dropbox_locked': bool,
                   'grading_scale_type': GradingScaleType,
                   'show_rubric': bool,
                   'display_weight': int,
                   'assignment_type': str,  # Undocumented
                   'web_url': str,
                   # Can just use len(asmt.assignees)
                   # 'num_assignees': int,
                   'assignees': list,  # TODO: needs access to "self"
                   'grading_group_ids': list,  # TODO: add GradingGroup
                   'last_updated': lambda s: datetime.fromtimestamp(int(s)),
                   'completion_status': str}

    # TODO: needs access to "self"
    # folder = LazyProperty('folder_id', lambda fid: Folder(fid, realm=self.realm))


class Message(RestObject):
    _REST_PATH = None
    _PROPERTIES = {'id': int,
                   'subject': str,
                   'last_updated': datetime.fromtimestamp,
                   'mid': int,  # Undocumented
                   'message': str}

    recipients = LazyProperty('recipient_ids', csv_to_list(int, User))
    author = LazyProperty('author_id', User)
    unread = LazyProperty('message_status', lambda s: s != 'read')


class MessageThread(RestObject):
    _REST_PATH = '/messages/{folder}/{id}'

    id = LazyProperty('id', int)
    messages = LazyProperty('message', lambda arr: [Message(d) for d in arr])

    def __init__(self, *args, folder=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder = folder
        # XXX this is a hack, since the original contains {'message': None} and
        # prevents a reload because the key is present
        del self._data['message']
