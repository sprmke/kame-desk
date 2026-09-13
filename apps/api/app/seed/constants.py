"""Synthetic demo data — never use real patient information."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

DEMO_PASSWORD = "password123"

# example.com passes Pydantic EmailStr; .local is rejected and breaks /auth/login (422).
OWNER_EMAIL = "demo@example.com"
DOCTOR2_EMAIL = "dr.santos@example.com"
RECEPTION_EMAIL = "reception@example.com"
ADMIN_EMAIL = "admin@example.com"
PLATFORM_EMAIL = "platform@example.com"
DOCTOR_B_EMAIL = "dr.reyes@example.com"
RECEPTION_B_EMAIL = "reception.bgc@example.com"

LEGACY_DEMO_EMAILS = (
    "demo@doctordesk.local",
    "dr.santos@doctordesk.local",
    "reception@doctordesk.local",
    "admin@doctordesk.local",
)

DEMO_EMAILS: tuple[str, ...] = (
    OWNER_EMAIL,
    DOCTOR2_EMAIL,
    RECEPTION_EMAIL,
    ADMIN_EMAIL,
    PLATFORM_EMAIL,
    DOCTOR_B_EMAIL,
    RECEPTION_B_EMAIL,
    *LEGACY_DEMO_EMAILS,
)

CLINIC_NAME = "Makati Family Clinic"
CLINIC_SLUG = "makati-family-clinic"
BRANCH_CLINIC_NAME = "Makati Family Clinic BGC"
BRANCH_CLINIC_SLUG = "makati-family-clinic-bgc"
ORG_NAME = "Makati Family Group"
ORG_SLUG = "makati-family-group"
DEMO_CLINIC_SLUGS: tuple[str, ...] = (CLINIC_SLUG, BRANCH_CLINIC_SLUG)

WORKING_HOURS: dict[str, dict[str, str | bool]] = {
    "mon": {"open": "08:00", "close": "17:00", "closed": False},
    "tue": {"open": "08:00", "close": "17:00", "closed": False},
    "wed": {"open": "08:00", "close": "17:00", "closed": False},
    "thu": {"open": "08:00", "close": "17:00", "closed": False},
    "fri": {"open": "08:00", "close": "17:00", "closed": False},
    "sat": {"open": "09:00", "close": "13:00", "closed": False},
    "sun": {"open": "09:00", "close": "12:00", "closed": True},
}

NOTIFICATION_PREFERENCES: dict = {
    "email_enabled": True,
    "sms_enabled": False,
    "confirmation_enabled": True,
    "reminder_24h_enabled": True,
    "reminder_2h_enabled": True,
    "sender_name": "Makati Family Clinic",
    "chronic_condition_rules": [
        {"condition": "Hypertension", "interval_months": 6},
        {"condition": "Type 2 Diabetes", "interval_months": 3},
    ],
}

RECEIPT_NUMBERING = {"prefix": "INV-", "next_number": 56, "pad_width": 4}
BRANCH_RECEIPT_NUMBERING = {"prefix": "BGC-", "next_number": 12, "pad_width": 4}

BIR_COMPLIANCE = {
    "tin": "123-456-789-000",
    "registered_name": "Makati Family Clinic Inc.",
    "registered_address": "Unit 402, Ayala Triangle Gardens Tower, Makati City",
    "vat_registered": True,
    "compliance_mode": "ptu",
    "accreditation_number": "PTU-MKT-2024-00881",
    "accreditation_valid_until": "2027-12-31",
}

GROWTH_SETTINGS = {
    "google_review_link": "https://g.page/makati-family-clinic/review",
    "review_requests_enabled": True,
    "doh_accreditation_number": "DOH-NCR-CLN-4412",
    "doh_accreditation_valid_until": "2027-06-30",
}


@dataclass(frozen=True)
class PatientFixture:
    full_name: str
    birthdate: date
    sex: str
    contact_number: str
    email: str | None
    allergies: list[dict]
    chronic_conditions: list[str]
    medical_history: str
    no_show_count: int = 0
    is_archived: bool = False
    reminders_opted_out: bool = False
    civil_status: str | None = None
    occupation: str | None = None
    insurance_info: dict | None = None
    family_history: str | None = None
    surgical_history: str | None = None
    vaccination_history: list[dict] = field(default_factory=list)


PATIENTS: list[PatientFixture] = [
    PatientFixture(
        full_name="Maria Santos",
        birthdate=date(1978, 3, 14),
        sex="Female",
        contact_number="+639171111001",
        email="maria.santos@example.com",
        allergies=[{"substance": "Penicillin", "reaction": "Rash", "severity": "moderate"}],
        chronic_conditions=["Hypertension", "Type 2 Diabetes"],
        medical_history="Hypertension since 2015. On maintenance meds.",
        civil_status="Married",
        occupation="Accountant",
        insurance_info={"provider": "Maxicare", "member_id": "MX-881001", "payer_type": "hmo"},
        family_history="Mother: type 2 diabetes. Father: hypertension.",
        vaccination_history=[{"name": "COVID-19 booster", "date": "2025-11-02"}],
    ),
    PatientFixture(
        full_name="Juan Dela Cruz",
        birthdate=date(1965, 7, 22),
        sex="Male",
        contact_number="+639171111002",
        email="juan.delacruz@example.com",
        allergies=[],
        chronic_conditions=["Type 2 Diabetes"],
        medical_history="Diabetes mellitus type 2, diet-controlled.",
        civil_status="Married",
        occupation="Retired teacher",
        insurance_info={
            "provider": "PhilHealth",
            "member_id": "PH-19650722",
            "payer_type": "philhealth",
        },
    ),
    PatientFixture(
        full_name="Ana Reyes",
        birthdate=date(2018, 11, 5),
        sex="Female",
        contact_number="+639171111003",
        email=None,
        allergies=[{"substance": "Shellfish", "reaction": "Hives", "severity": "mild"}],
        chronic_conditions=[],
        medical_history="Pediatric well-child visits.",
        civil_status="Single",
        vaccination_history=[{"name": "MMR", "date": "2020-01-12"}],
    ),
    PatientFixture(
        full_name="Roberto Garcia",
        birthdate=date(1990, 1, 30),
        sex="Male",
        contact_number="+639171111004",
        email="roberto.garcia@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Seasonal allergic rhinitis.",
        civil_status="Single",
        occupation="Software engineer",
    ),
    PatientFixture(
        full_name="Elena Mendoza",
        birthdate=date(1985, 9, 12),
        sex="Female",
        contact_number="+639171111005",
        email="elena.mendoza@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Recurrent migraine headaches.",
        civil_status="Married",
        occupation="Graphic designer",
        insurance_info={"provider": "Medicard", "member_id": "MD-44219", "payer_type": "hmo"},
    ),
    PatientFixture(
        full_name="Carlos Villanueva",
        birthdate=date(1955, 4, 8),
        sex="Male",
        contact_number="+639171111006",
        email=None,
        allergies=[],
        chronic_conditions=["Hypertension", "Hyperlipidemia"],
        medical_history="Post-MI 2019. On aspirin and statin.",
        civil_status="Widowed",
        occupation="Retired",
        surgical_history="CABG 2019.",
    ),
    PatientFixture(
        full_name="Patricia Lim",
        birthdate=date(1992, 6, 19),
        sex="Female",
        contact_number="+639171111007",
        email="patricia.lim@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Prenatal care, G1P0.",
        civil_status="Married",
        occupation="Marketing manager",
    ),
    PatientFixture(
        full_name="Miguel Torres",
        birthdate=date(2008, 12, 3),
        sex="Male",
        contact_number="+639171111008",
        email=None,
        allergies=[{"substance": "Ibuprofen", "reaction": "GI upset", "severity": "mild"}],
        chronic_conditions=["Asthma"],
        medical_history="Mild persistent asthma.",
        civil_status="Single",
    ),
    PatientFixture(
        full_name="Grace Tan",
        birthdate=date(1970, 2, 28),
        sex="Female",
        contact_number="+639171111009",
        email="grace.tan@example.com",
        allergies=[],
        chronic_conditions=["Hypothyroidism"],
        medical_history="On levothyroxine.",
        civil_status="Married",
        occupation="Bank officer",
        insurance_info={"provider": "Intellicare", "member_id": "IC-77012", "payer_type": "hmo"},
    ),
    PatientFixture(
        full_name="Ramon Aquino",
        birthdate=date(1988, 8, 17),
        sex="Male",
        contact_number="+639171111010",
        email="ramon.aquino@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Low back pain, office worker.",
        no_show_count=2,
        civil_status="Single",
        occupation="Call center supervisor",
    ),
    PatientFixture(
        full_name="Sofia Cruz",
        birthdate=date(2015, 5, 25),
        sex="Female",
        contact_number="+639171111011",
        email=None,
        allergies=[],
        chronic_conditions=[],
        medical_history="School clearance exams.",
        civil_status="Single",
    ),
    PatientFixture(
        full_name="Daniel Ong",
        birthdate=date(1960, 10, 11),
        sex="Male",
        contact_number="+639171111012",
        email="daniel.ong@example.com",
        allergies=[],
        chronic_conditions=["Hypertension", "Gout"],
        medical_history="Gout flares twice yearly.",
        civil_status="Married",
        occupation="Driver",
    ),
    PatientFixture(
        full_name="Isabel Ramos",
        birthdate=date(1995, 3, 7),
        sex="Female",
        contact_number="+639171111013",
        email="isabel.ramos@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Acne vulgaris.",
        civil_status="Single",
        occupation="Nurse",
    ),
    PatientFixture(
        full_name="Fernando Bautista",
        birthdate=date(1948, 12, 1),
        sex="Male",
        contact_number="+639171111014",
        email=None,
        allergies=[],
        chronic_conditions=["Hypertension", "Type 2 Diabetes", "CKD stage 2"],
        medical_history="Geriatric follow-up.",
        civil_status="Married",
        occupation="Retired",
        insurance_info={
            "provider": "PhilHealth",
            "member_id": "PH-19481201",
            "payer_type": "philhealth",
        },
    ),
    PatientFixture(
        full_name="Liza Fernandez",
        birthdate=date(1982, 7, 9),
        sex="Female",
        contact_number="+639171111015",
        email="liza.fernandez@example.com",
        allergies=[{"substance": "Sulfa drugs", "reaction": "Rash", "severity": "moderate"}],
        chronic_conditions=[],
        medical_history="UTI history.",
        civil_status="Married",
        occupation="Teacher",
        reminders_opted_out=True,
    ),
    PatientFixture(
        full_name="Paolo Navarro",
        birthdate=date(1991, 11, 21),
        sex="Male",
        contact_number="+639171111016",
        email="paolo.navarro@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Generalized anxiety. Follows up for counseling.",
        civil_status="Single",
        occupation="Writer",
    ),
    PatientFixture(
        full_name="Camille Sy",
        birthdate=date(1987, 4, 2),
        sex="Female",
        contact_number="+639171111017",
        email="camille.sy@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Contact dermatitis on both hands.",
        civil_status="Married",
        occupation="Chef",
    ),
    PatientFixture(
        full_name="Andres Villar",
        birthdate=date(1973, 8, 30),
        sex="Male",
        contact_number="+639171111018",
        email="andres.villar@example.com",
        allergies=[],
        chronic_conditions=["Hypertension"],
        medical_history="Moved clinics. Record kept for history.",
        civil_status="Married",
        occupation="Engineer",
        is_archived=True,
    ),
    PatientFixture(
        full_name="Helena Go",
        birthdate=date(1998, 1, 15),
        sex="Female",
        contact_number="+639171111019",
        email="helena.go@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Annual physical. Clinic membership plan.",
        civil_status="Single",
        occupation="Analyst",
        insurance_info={"provider": "Maxicare", "member_id": "MX-991019", "payer_type": "hmo"},
    ),
    PatientFixture(
        full_name="Victor Ramos",
        birthdate=date(2012, 9, 8),
        sex="Male",
        contact_number="+639171111020",
        email=None,
        allergies=[],
        chronic_conditions=[],
        medical_history="Dental consult for molar caries.",
        civil_status="Single",
    ),
]

BRANCH_PATIENTS: list[PatientFixture] = [
    PatientFixture(
        full_name="Nina Castillo",
        birthdate=date(2016, 2, 14),
        sex="Female",
        contact_number="+639171222001",
        email=None,
        allergies=[],
        chronic_conditions=[],
        medical_history="Well-child and vaccines.",
        civil_status="Single",
    ),
    PatientFixture(
        full_name="Leo Marquez",
        birthdate=date(1984, 5, 9),
        sex="Male",
        contact_number="+639171222002",
        email="leo.marquez@example.com",
        allergies=[],
        chronic_conditions=["Asthma"],
        medical_history="Exercise-induced asthma.",
        civil_status="Married",
        occupation="Sales",
        insurance_info={"provider": "Maxicare", "member_id": "MX-BGC-02", "payer_type": "hmo"},
    ),
    PatientFixture(
        full_name="Andrea Chua",
        birthdate=date(1993, 10, 18),
        sex="Female",
        contact_number="+639171222003",
        email="andrea.chua@example.com",
        allergies=[],
        chronic_conditions=[],
        medical_history="Prenatal transfer from Makati branch.",
        civil_status="Married",
        occupation="Architect",
    ),
    PatientFixture(
        full_name="Benjamin Yap",
        birthdate=date(1971, 12, 4),
        sex="Male",
        contact_number="+639171222004",
        email="benjamin.yap@example.com",
        allergies=[],
        chronic_conditions=["Hypertension"],
        medical_history="Office BP checks.",
        civil_status="Married",
        occupation="Lawyer",
    ),
    PatientFixture(
        full_name="Katrina Uy",
        birthdate=date(2001, 7, 27),
        sex="Female",
        contact_number="+639171222005",
        email="katrina.uy@example.com",
        allergies=[{"substance": "Peanuts", "reaction": "Anaphylaxis", "severity": "severe"}],
        chronic_conditions=[],
        medical_history="Carries epinephrine auto-injector.",
        civil_status="Single",
        occupation="Student",
    ),
    PatientFixture(
        full_name="Oscar Padilla",
        birthdate=date(1959, 3, 3),
        sex="Male",
        contact_number="+639171222006",
        email=None,
        allergies=[],
        chronic_conditions=["Type 2 Diabetes"],
        medical_history="BGC follow-up for HbA1c.",
        civil_status="Married",
        occupation="Retired",
    ),
]

SERVICE_FEES: list[tuple[str, Decimal, str | None, int | None]] = [
    ("General consultation", Decimal("500.00"), "consultation", 30),
    ("Follow-up visit", Decimal("350.00"), "consultation", 20),
    ("ECG", Decimal("450.00"), "procedure", 15),
    ("CBC panel", Decimal("350.00"), "lab", None),
    ("Urinalysis", Decimal("150.00"), "lab", None),
    ("Nebulization", Decimal("400.00"), "procedure", 20),
    ("Prenatal consult", Decimal("700.00"), "consultation", 30),
    ("Pediatric consult", Decimal("550.00"), "consultation", 30),
]

BRANCH_SERVICE_FEES: list[tuple[str, Decimal, str | None, int | None]] = [
    ("General consultation", Decimal("550.00"), "consultation", 30),
    ("Pediatric consult", Decimal("600.00"), "consultation", 30),
    ("Follow-up visit", Decimal("380.00"), "consultation", 20),
]

SOAP_DIAGNOSES: list[tuple[str, str, str, str, str, str]] = [
    (
        "Hypertension, uncontrolled",
        "Patient reports occasional headaches. Compliance with meds is fair.",
        "BP 152/96. Heart regular. No edema.",
        "Hypertension, uncontrolled",
        "Adjust amlodipine. Low-salt diet. Recheck in 2 weeks.",
        "I10",
    ),
    (
        "Type 2 diabetes mellitus",
        "Increased thirst and polyuria for 2 weeks.",
        "FBS 168. No ketones. Feet intact.",
        "Type 2 diabetes mellitus",
        "Start metformin. Diet counseling. HbA1c in 3 months.",
        "E11.9",
    ),
    (
        "Migraine without aura",
        "Recurrent throbbing headache, photophobia, nausea.",
        "Neuro exam normal. No neck stiffness.",
        "Migraine without aura",
        "Sumatriptan PRN. Sleep hygiene. Avoid triggers.",
        "G43.0",
    ),
    (
        "Acute upper respiratory infection",
        "Cough and colds for 3 days. No fever today.",
        "Throat mildly erythematous. Lungs clear.",
        "Acute upper respiratory infection",
        "Symptomatic care. Return if fever or dyspnea.",
        "J06.9",
    ),
    (
        "Low back pain",
        "Mechanical back pain after lifting. No leg weakness.",
        "Paravertebral tenderness. SLR negative.",
        "Low back pain",
        "NSAIDs short course. Stretching. Ergonomic advice.",
        "M54.5",
    ),
    (
        "Mild persistent asthma",
        "Wheeze after running. Uses salbutamol 2-3x/week.",
        "O2 sat 98%. Expiratory wheeze, mild.",
        "Mild persistent asthma",
        "Continue controller. Review inhaler technique.",
        "J45.909",
    ),
    (
        "Urinary tract infection",
        "Dysuria and frequency for 2 days. No flank pain.",
        "Afebrile. Suprapubic tenderness. UA nitrite positive.",
        "Acute cystitis",
        "Empiric antibiotic 5 days. Increase fluids.",
        "N39.0",
    ),
    (
        "Acne vulgaris",
        "Facial breakouts for 6 months. Tried OTC benzoyl peroxide.",
        "Inflammatory papules on cheeks and chin.",
        "Acne vulgaris, moderate",
        "Start topical retinoid. Sun protection.",
        "L70.0",
    ),
]
