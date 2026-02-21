"""
One-time fix: set company_id on projects where company_id is NULL.
Uses created_by.employee_get.employee_work_info.company_id when available.
Run: python manage.py shell < fix_project_company_null.py
"""
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")
django.setup()

from project.models import Project
from employee.models import Employee

updated = 0
skipped = 0
for p in Project.objects.filter(company_id__isnull=True):
    company = None
    if p.created_by and getattr(p.created_by, "employee_get", None):
        emp = p.created_by.employee_get
        if emp and getattr(emp, "employee_work_info", None) and emp.employee_work_info.company_id:
            company = emp.employee_work_info.company_id
    if company:
        p.company_id = company
        p.save(update_fields=["company_id"])
        updated += 1
        print(f"Updated project id={p.id} title={p.title!r} -> company_id={company.id}")
    else:
        skipped += 1
        print(f"Skipped project id={p.id} title={p.title!r} (no company from created_by)")

print(f"Done: updated={updated}, skipped={skipped}")
