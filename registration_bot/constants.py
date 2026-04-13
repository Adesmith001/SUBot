"""Shared constants for registration and admin flows."""

(
    AWAITING_FORM_STATUS,
    AWAITING_REG_NO_CHECK,
    REG_FIELD_INPUT,
    AWAITING_GENDER,
    AWAITING_COLLEGE,
    AWAITING_SUBUNIT,
    AWAITING_CONTACT,
    AWAITING_SEMESTER,
    AWAITING_DOB_YEAR,
    AWAITING_DOB_MONTH,
    AWAITING_DOB_DAY,
) = range(11)

REGISTRATION_DATA_KEY = "registration_data"
REGISTRATION_INDEX_KEY = "reg_field_idx"
SEMESTER_KEY = "semester"
ADMIN_ACTION_KEY = "admin_action"
REG_NO_LOOKUP_MODE_KEY = "reg_no_lookup_mode"

REG_FIELDS_CONFIG = [
    {"name": "SURNAME", "type": "text"},
    {"name": "OTHER NAMES", "type": "text"},
    {"name": "DATE OF BIRTH", "type": "dob"},
    {"name": "GENDER", "type": "inline_keyboard", "options": ["Male", "Female"]},
    {"name": "REGISTRATION NUMBER", "type": "text"},
    {"name": "COLLEGE", "type": "inline_keyboard", "options": ["CST", "COE", "CLDS", "CMSS"]},
    {
        "name": "PROGRAM",
        "type": "inline_keyboard",
        "options": [
            "ACCOUNTING",
            "APPLIED BIOLOGY AND BIOTECHNOLOGY",
            "ARCHITECTURE",
            "BIOCHEMISTRY",
            "BUILDING TECHNOLOGY",
            "BUSINESS ADMINISTRATION",
            "CHEMICAL ENGINEERING",
            "CIVIL ENGINEERING",
            "COMPUTER ENGINEERING",
            "COMPUTER SCIENCE",
            "ECONOMICS",
            "ELECTRICAL AND ELECTRONICS ENGINEERING",
            "ENGLISH",
            "ESTATE MANAGEMENT",
            "FINANCE",
            "FINTECH",
            "INDUSTRIAL CHEMISTRY",
            "INDUSTRIAL MATHEMATICS",
            "INDUSTRIAL PHYSICS",
            "INDUSTRIAL RELATIONS AND HUMAN RESOURCE MANAGEMENT",
            "INFORMATION AND COMMUNICATIONS ENGINEERING",
            "INTERNATIONAL RELATIONS",
            "MANAGEMENT INFORMATION SYSTEMS",
            "MARKETING",
            "MASS COMMUNICATION",
            "MECHANICAL ENGINEERING",
            "MICROBIOLOGY",
            "PETROLEUM ENGINEERING",
            "POLICY AND STRATEGIC STUDIES",
            "POLITICAL SCIENCE",
            "PSYCHOLOGY",
            "SOCIOLOGY",
        ],
    },
    {
        "name": "LEVEL",
        "type": "inline_keyboard",
        "options": [
            "100 LEVEL",
            "200 LEVEL",
            "300 LEVEL",
            "400 LEVEL (NOT FINAL YEAR)",
            "400 LEVEL",
            "500 LEVEL",
        ],
    },
    {
        "name": "HALL",
        "type": "inline_keyboard",
        "options": ["JOSEPH", "JOSHUA", "DEBORAH", "LYDIA", "MARY", "DORCAS", "PAUL", "PETER", "DANIEL"],
    },
    {"name": "ROOM NUMBER", "type": "text"},
    {
        "name": "SUBUNIT",
        "type": "inline_keyboard",
        "options": [
            "ALPHA CHAPEL",
            "OMEGA CHAPEL",
            "COBWEBS AND DUSTBINS",
            "ALTAR AND TOILET",
            "WINDOWS AND DOORS",
            "ROYAL CHAIRS",
            "STORE",
        ],
    },
    {"name": "ARE YOU A NEW MEM", "type": "inline_keyboard", "options": ["Yes", "No"]},
]

SUBUNIT_OPTIONS = next(
    field["options"] for field in REG_FIELDS_CONFIG if field["name"] == "SUBUNIT"
)
