"""Built-in specialty SOAP templates (global catalog)."""

SPECIALTY_TEMPLATES = [
    {
        "template_key": "general",
        "name": "General",
        "schema_version": 1,
        "description": "Standard S/O/A/P only",
    },
    {
        "template_key": "dental",
        "name": "Dental",
        "schema_version": 1,
        "description": "Tooth chart fields",
    },
    {
        "template_key": "pediatric",
        "name": "Pediatric",
        "schema_version": 1,
        "description": "Growth percentiles",
    },
    {
        "template_key": "obgyn",
        "name": "OB-GYN",
        "schema_version": 1,
        "description": "Obstetric history and EDD",
    },
    {
        "template_key": "psychiatry",
        "name": "Psychiatry",
        "schema_version": 1,
        "description": "Mental status and risk",
    },
    {
        "template_key": "dermatology",
        "name": "Dermatology",
        "schema_version": 1,
        "description": "Lesion location and type",
    },
]

ICD10_SUGGESTIONS = [
    {"code": "J06.9", "label": "Acute upper respiratory infection"},
    {"code": "I10", "label": "Essential hypertension"},
    {"code": "E11.9", "label": "Type 2 diabetes mellitus"},
    {"code": "J45.909", "label": "Asthma, unspecified"},
    {"code": "M54.5", "label": "Low back pain"},
    {"code": "N39.0", "label": "Urinary tract infection"},
    {"code": "J02.9", "label": "Acute pharyngitis"},
    {"code": "A09", "label": "Infectious gastroenteritis"},
    {"code": "L30.9", "label": "Dermatitis, unspecified"},
    {"code": "F32.9", "label": "Depressive episode, unspecified"},
    {"code": "O80", "label": "Encounter for full-term uncomplicated delivery"},
    {"code": "Z34.90", "label": "Supervision of normal pregnancy"},
]
