from datetime import datetime
from enum import Enum, Flag, auto


def parsetime(s):
    if not s:
        return None
    return datetime.strptime(s, '%H:%M').time()

def parsedate(s):
    if not s:
        return None
    return datetime.strptime(s, '%Y-%m-%d').date()


def csv_to_list(*fns):
    def _process(csv):
        values = []
        for value in filter(bool, csv.split(',')):
            for fn in fns:
                # Allow callable to be specified as string so we can use a
                # class in its own static definition.
                if isinstance(fn, str):
                    fn = globals()[fn]
                value = fn(value)
            values.append(value)
        return values
    return _process


def LazyProperty(name, *fns):
    def _get(self):
        # XXX If the property isn't there, this will attempt reload every time
        # Perhaps track in RestObject whether fully loaded and don't attempt again.
        if name not in self._data:
            self.reload()
        value = self._data.get(name)
        if value is not None:
            for fn in fns:
                value = fn(value)
        return value
    return property(_get)


class RestObject:
    API = None
    _REST_PATH = ''
    _PROPERTIES = {}

    @classmethod
    def set_api(cls, api):
        cls.API = api

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, ctor in cls._PROPERTIES.items():
            setattr(cls, name, LazyProperty(name, ctor))

    def __init__(self, id=None, *args, data=None, **kwargs):
        super().__init__(*args, **kwargs)
        if data is None:
            data = {}
        if id is not None:
            data['id'] = id
        self._data = data

    def __getitem__(self, name):
        return getattr(self, name)

    def __str__(self):
        return str(self['title'])

    def reload(self):
        path = self._REST_PATH.format_map(self)
        self._data.update(self.API._get(path))


class School(RestObject):
    _REST_PATH = '/schools/{school_id}'
    _PROPERTIES = {'title': str,
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

    school_id = LazyProperty('id', int)


class Building(RestObject):
    # Not a typo
    _REST_PATH = '/schools/{building_id}'
    _PROPERTIES = {'title': str,
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

    building_id = LazyProperty('id', int)


class RoleType(Enum):
    ORGANIZATION = 1
    BUILDING = 2


class Role(RestObject):
    _REST_PATH = '/roles/{role_id}'
    _PROPERTIES = {'title': str,
                   'faculty': bool,
                   'role_type': RoleType}

    role_id = LazyProperty('id', int)


class PrivacyLevel(Enum):
    everyone = auto()
    school = auto()
    building = auto()
    group = auto()
    custom = auto()


class DictableFlag(Flag):
    @classmethod
    def from_dict(cls, d):
        total = 0
        for k, v in d.items():
            if v:
                total |= getattr(cls, k).value
        return cls(total)

    def to_dict(self):
        return {opt.name: int(opt in self) for opt in type(self)}


class GroupOptions(DictableFlag):
    member_post = auto()
    member_post_comment = auto()
    create_discussion = auto()
    create_files = auto()
    invite_type = auto()


class Group(RestObject):
    _REST_PATH = '/groups/{group_id}'
    _PROPERTIES = {'title': str,
                   'description': str,
                   'website': str,
                   'access_code': str,
                   # 'category': GroupCategory,
                   'options': GroupOptions.from_dict,
                   'group_code': str,
                   'privacy_level': PrivacyLevel.__getattr__,
                   'picture_url': str,
                   'admin': bool}

    group_id = LazyProperty('id', int)
    school = LazyProperty('school_id', int, School)
    building = LazyProperty('building_id', int, Building)


class Gender(Enum):
    M = auto()
    F = auto()


class UserPermissions(DictableFlag):
    # Others?
    is_directory_public = auto()
    allow_connections = auto()


# TODO: investigate requesting with ?extended=TRUE
class User(RestObject):
    _REST_PATH = '/users/{user_id}'
    _PROPERTIES = {'synced': bool,
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

    user_id = LazyProperty('id', int)
    school = LazyProperty('school_id', int, School)
    building = LazyProperty('building_id', int, Building)
    role = LazyProperty('role_id', int, Role)
    # Undocumented:
    use_preferred_first_name = LazyProperty('use_preferred_first_name',
                                            int, bool)

    def __str__(self):
        return self.name_display


class GradingPeriod(RestObject):
    _REST_PATH = '/gradingperiods/{gradingperiod_id}'
    _PROPERTIES = {'title': str,
                   'start': parsedate,
                   'end': parsedate,
                   'active': bool,
                   # Undocumented from here down
                   'has_children': bool,
                   'parent': int}

    gradingperiod_id = LazyProperty('id', int)


class SubjectArea(Enum):
    OTHER = 0
    HEALTH_AND_PHYSICAL_EDUCATION = 1
    LANGUAGE = 2
    MATHEMATICS = 3
    PROFESSIONAL_DEVELOPMENT = 4
    SCIENCE = 5
    SOCIAL_STUDIES = 6
    SPECIAL_EDUCATION = 7
    TECHNOLOGY = 8
    ARTS = 9


class Course(RestObject):
    _REST_PATH = '/courses/{course_id}'
    _PROPERTIES = {'title': str,
                   'course_code': str,
                   'department': str,
                   'description': str,
                   'credits': int,
                   'subject_area': SubjectArea,
                   'grade_level_range_start': int,
                   'grade_level_range_end': int,
                   'synced': bool}

    course_id = LazyProperty('id', int)
    building = LazyProperty('building_id', int, Building)


class Section(RestObject):
    _REST_PATH = '/sections/{section_id}'
    _PROPERTIES = {'course_title': str,
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

    section_id = LazyProperty('id', int)
    course = LazyProperty('course_id', int, Course)
    school = LazyProperty('school_id', int, School)
    building = LazyProperty('building_id', int, Building)
    title = LazyProperty('section_title', str)


class EnrollmentStatus(Enum):
    ACTIVE = 1
    EXPIRED = 2
    INVITED = 3
    REQUESTED = 4
    ARCHIVED = 5


class Enrollment(RestObject):
    _REST_PATH = '/{realm}s/{realm_id}/enrollments/{enrollment_id}'
    _PROPERTIES = {'school_uid': str,
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
                   'realm': str,
                   'realm_id': int,
                   # Undocumented, only when realm='section'
                   'enrollment_source': int}

    enrollment_id = LazyProperty('id', int)
    user = LazyProperty('uid', int, User)
