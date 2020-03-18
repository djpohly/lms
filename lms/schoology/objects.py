from enum import Enum, Flag, auto


def LazyProperty(name, *fns):
    def _get(self):
        if name not in self.data:
            self.reload()
        value = self.data[name]
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
        self.data = data

    def __getitem__(self, name):
        return getattr(self, name)

    def __str__(self):
        return str(self['title'])

    def id(self):
        """Retrieves the object's unique ID from its data"""

        # Default to the value of the 'id' field
        return (self.data['id'],)

    def reload(self):
        path = self._REST_PATH.format_map(self)
        self.data.update(self.API._get(path))


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
    user_id = LazyProperty('id', int)
    school = LazyProperty('school_id', int, School)
    building = LazyProperty('building_id', int, Building)
    role = LazyProperty('role_id', int, Role)
    # Undocumented:
    use_preferred_first_name = LazyProperty('use_preferred_first_name',
                                            int, bool)
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

    def __str__(self):
        return self.name_display
