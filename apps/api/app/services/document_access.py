from fastapi import HTTPException

from app.models import ClinicMembership


def assert_template_admin(membership: ClinicMembership) -> None:
    if membership.role in ("owner", "admin"):
        return
    raise HTTPException(status_code=403, detail="Template admin access denied")


def assert_document_read(membership: ClinicMembership) -> None:
    if membership.role in ("owner", "admin", "doctor", "reception"):
        return
    raise HTTPException(status_code=403, detail="Document access denied")


def assert_document_write(membership: ClinicMembership) -> None:
    if membership.role in ("owner", "doctor"):
        return
    raise HTTPException(status_code=403, detail="Document write not allowed")
