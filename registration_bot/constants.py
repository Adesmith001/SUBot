"""Shared constants for registration and admin flows."""

REG_FIELD_INPUT, AWAITING_GENDER, AWAITING_COLLEGE, AWAITING_SUBUNIT, AWAITING_CONTACT, AWAITING_SEMESTER, AWAITING_REGISTERED_ALPHA = range(7)

REGISTRATION_DATA_KEY = "registration_data"
REGISTRATION_INDEX_KEY = "reg_field_idx"
SEMESTER_KEY = "semester"
ADMIN_ACTION_KEY = "admin_action"

REG_FIELDS_CONFIG = [
    {"name": "SURNAME", "type": "text"},
    {"name": "OTHER NAMES", "type": "text"},
    {"name": "DATE OF BIRTH", "type": "dob"},
    {"name": "GENDER", "type": "inline_keyboard", "options": ["Male", "Female"]},
    {"name": "REGISTRATION NUMBER", "type": "text"},
    {
        "name": "COLLEGE",
        "type": "inline_keyboard",
        "options": [
            "College of Science and Technology",
            "College of Engineering",
            "College of Management and Social Science",
            "College of Leadersip Developement Studies",
        ],
    },
    {"name": "PROGRAM", "type": "text"},
    {"name": "LEVEL", "type": "text"},
    {
        "name": "SUBUNIT",
        "type": "inline_keyboard",
        "options": [
            "Alpha",
            "Omega",
            "Cobbwebs and Dustbins",
            "Altar and Toilet",
            "Windows and Doors",
            "Royal Chairs",
            "Store",
        ],
    },
    {"name": "HALL & ROOM NUMBER", "type": "text"},
]

SUBUNIT_OPTIONS = next(
    field["options"] for field in REG_FIELDS_CONFIG if field["name"] == "SUBUNIT"
)

