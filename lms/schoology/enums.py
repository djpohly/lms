from enum import Enum, auto
from .util import DictableFlag


class EnrollmentStatus(Enum):
    ACTIVE = 1
    EXPIRED = 2
    INVITED = 3
    REQUESTED = 4
    ARCHIVED = 5


class Gender(Enum):
    M = auto()
    F = auto()


class GroupOptions(DictableFlag):
    member_post = auto()
    member_post_comment = auto()
    create_discussion = auto()
    create_files = auto()
    invite_type = auto()


class PrivacyLevel(Enum):
    everyone = auto()
    school = auto()
    building = auto()
    group = auto()
    custom = auto()


class RoleType(Enum):
    ORGANIZATION = 1
    BUILDING = 2


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


class UserPermissions(DictableFlag):
    # Others?
    is_directory_public = auto()
    allow_connections = auto()
