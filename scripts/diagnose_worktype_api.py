#!/usr/bin/env python
"""
Diagnose: GET /api/v1/base/worktypes/ vs Django Admin mismatch.
Answers:
  1. What JSON would GET return for Dileesh?
  2. Does the API response contain the newly created WorkType?
  3. effective_company_id for Dileesh
  4. WorkType records in DB: company_id linked same as Dileesh?
  5. Any extra filtering (is_active, archived, etc.)?

Run from project root:
  python manage.py shell
  >>> exec(open('scripts/diagnose_worktype_api.py').read())
"""

import json
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")
django.setup()

from base.models import WorkType, Company
from employee.models import Employee
from horilla_api.api_serializers.base.serializers import WorkTypeSerializer


def main():
    print("=" * 60)
    print("WORKTYPE API DIAGNOSTIC (Dileesh / GET /api/v1/base/worktypes/)")
    print("=" * 60)

    # --- Resolve Dileesh employee and effective_company_id ---
    emp = Employee.objects.filter(employee_first_name__icontains="dileesh").first()
    if not emp:
        emp = Employee.objects.filter(employee_user_id__email__icontains="dileesh").first()
    if not emp:
        print("\n[!] No employee found with name/email containing 'dileesh'.")
        print("    Edit script to use another user (e.g. by email).")
        return

    company = getattr(emp, "get_company", None) and emp.get_company()
    effective_company_id = company.id if company else None
    company_name = company.company if company else None

    print("\n--- 3. effective_company_id for Dileesh ---")
    print(f"  Employee id: {emp.id}")
    print(f"  effective_company_id: {effective_company_id}")
    print(f"  Company name: {company_name or '(None)'}")

    # --- What GET list returns (same logic as WorkTypeView.get) ---
    work_types_qs = WorkType.objects.all()
    if effective_company_id is not None:
        work_types_qs = work_types_qs.filter(company_id=effective_company_id)

    print("\n--- 5. Extra filtering on queryset? ---")
    print("  WorkType model has NO is_active, archived, or permission filter on list.")
    print("  Only filter applied: company_id = effective_company_id (when not None).")

    serializer = WorkTypeSerializer(work_types_qs, many=True)
    api_response_json = serializer.data

    print("\n--- 1. JSON returned by GET /api/v1/base/worktypes/ (as Dileesh) ---")
    print(json.dumps(api_response_json, indent=2))

    print("\n--- 2. Does API response contain the newly created WorkType? ---")
    if api_response_json:
        print(f"  YES – API returns {len(api_response_json)} work type(s). IDs: {[x.get('id') for x in api_response_json]}")
    else:
        print("  NO – API returns EMPTY list. So frontend will show empty.")

    print("\n--- 4. WorkType records in DB vs Dileesh company ---")
    all_wts = WorkType.objects.all().order_by("-id")[:15]
    for wt in all_wts:
        company_ids = list(wt.company_id.values_list("id", flat=True))
        names = list(wt.company_id.values_list("company", flat=True))
        match = "MATCH" if effective_company_id in company_ids else "NO MATCH"
        print(f"  id={wt.id} work_type={wt.work_type!r} company_ids={company_ids} companies={names} -> {match}")

    print("\n" + "=" * 60)
    print("CONCLUSION: If API JSON is empty but Admin shows data, WorkType rows have")
    print("company_id M2M not including effective_company_id for this user.")
    print("=" * 60)


if __name__ == "__main__":
    main()
