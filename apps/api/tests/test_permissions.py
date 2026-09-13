from app.core.permissions import compute_permissions
from app.models import Clinic, ClinicMembership


def test_reception_without_soap_access():
    membership = ClinicMembership(role="reception", is_active=True)
    clinic = Clinic(name="Test", reception_can_view_soap=False)
    perms = compute_permissions(membership, clinic)
    assert "patients:chart_search" not in perms
    assert "outreach:view" in perms
    assert "documents:view" not in perms


def test_reception_with_soap_opt_in():
    membership = ClinicMembership(role="reception", is_active=True)
    clinic = Clinic(name="Test", reception_can_view_soap=True)
    perms = compute_permissions(membership, clinic)
    assert "patients:chart_search" in perms
    assert "chart_search:use" in perms


def test_doctor_has_clinical_not_outreach():
    membership = ClinicMembership(role="doctor", is_active=True)
    clinic = Clinic(name="Test")
    perms = compute_permissions(membership, clinic)
    assert "documents:view" in perms
    assert "outreach:view" not in perms
