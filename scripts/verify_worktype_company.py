#!/usr/bin/env python
"""
Verify WorkType company assignment and list API behavior.
Run from project root: python manage.py shell < scripts/verify_worktype_company.py
Or: python manage.py shell
    >>> exec(open('scripts/verify_worktype_company.py').read())

Checks:
1. WorkType records and their company_id (M2M) assignment
2. Employee Dileesh -> company
3. Which work types would be returned for that company (GET list filter)
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")
django.setup()

from base.models import WorkType
from employee.models import Employee

def main():
    print("=== 1. WorkType table: all records and company_id (M2M) ===\n")
    for wt in WorkType.objects.all().order_by("-id")[:20]:
        company_ids = list(wt.company_id.values_list("id", flat=True))
        company_names = list(wt.company_id.values_list("company", flat=True))
        print(f"  id={wt.id}  work_type={wt.work_type!r}  company_id={company_ids}  companies={company_names}")

    print("\n=== 2. Employee 'Dileesh' -> company ===\n")
    # Match by name or user email
    emp = Employee.objects.filter(employee_first_name__icontains="dileesh").first()
    if not emp:
        emp = Employee.objects.filter(employee_user_id__email__icontains="dileesh").first()
    if emp:
        company = getattr(emp, "get_company", None) and emp.get_company()
        if company:
            print(f"  Employee id={emp.id}  company_id={company.id}  company={company.company}")
        else:
            ew = getattr(emp, "employee_work_info", None)
            cid = ew.company_id_id if ew else None
            print(f"  Employee id={emp.id}  company (get_company)=None  employee_work_info.company_id_id={cid}")
    else:
        print("  No employee found with name/email containing 'dileesh'")

    print("\n=== 3. Work types returned by GET list for effective_company_id (e.g. 2) ===\n")
    effective_company_id = 2  # change if Dileesh's company is different
    if emp and getattr(emp, "get_company", None) and emp.get_company():
        effective_company_id = emp.get_company().id
    qs = WorkType.objects.filter(company_id=effective_company_id)
    print(f"  Filter: WorkType.objects.filter(company_id={effective_company_id})  count={qs.count()}")
    for wt in qs[:10]:
        print(f"    id={wt.id}  work_type={wt.work_type!r}")

    print("\nDone.")

if __name__ == "__main__":
    main()
