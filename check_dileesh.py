"""Run with: python manage.py shell < check_dileesh.py (or run from shell and paste)."""
from django.contrib.auth import get_user_model
from employee.models import Employee

User = get_user_model()
# React login user (Dileesh): username is email in this DB
username = "dileeshsai007@gmail.com"
try:
    u = User.objects.get(username=username)
except User.DoesNotExist:
    u = User.objects.filter(username__iexact="dileesh").first()
if u is None:
    print("User not found. Users with 'dil' in username:")
    for x in User.objects.filter(username__icontains="dil")[:10]:
        print("  ", x.id, x.username)
    raise SystemExit(1)

print("User ID:", u.id)
print("Username:", u.username)

emp = Employee.objects.filter(employee_user_id=u).first()
print("Employee found:", emp is not None)

if emp:
    print("Employee ID:", emp.id)
    wi = getattr(emp, "employee_work_info", None)
    company = wi.company_id if wi else None
    print("Company:", getattr(company, "company", None) if company else None)
