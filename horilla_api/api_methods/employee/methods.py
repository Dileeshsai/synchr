import re

from base.methods import eval_validate
from base.models import *
from employee.models import Employee


def get_next_available_badge_id():
    """
    Return a badge_id that does not exist in the DB (uses entire() to see all companies).
    Used as fallback when get_next_badge_id() produces a duplicate (e.g. company filter or race).
    """
    from base.context_processors import get_initial_prefix
    prefix = get_initial_prefix(None)["get_initial_prefix"] or "PEP"
    # Use entire() so we see all employees across companies (badge_id must be globally unique)
    qs = getattr(Employee.objects, "entire", lambda: Employee.objects.all())()
    existing = (
        qs.exclude(badge_id__isnull=True)
        .exclude(badge_id="")
        .filter(badge_id__istartswith=prefix)
        .values_list("badge_id", flat=True)
    )
    max_num = 0
    for bid in existing:
        digits = "".join(c for c in str(bid) if c.isdigit())
        if digits:
            try:
                max_num = max(max_num, int(digits))
            except ValueError:
                pass
    return f"{prefix}{max_num + 1:04d}"


def get_next_badge_id():
    """
    This method is used to generate badge id
    """
    from base.context_processors import get_initial_prefix
    from employee.methods.methods import get_ordered_badge_ids

    prefix = get_initial_prefix(None)["get_initial_prefix"]
    data = get_ordered_badge_ids()
    result = []
    try:
        for sublist in data:
            for item in sublist:
                if isinstance(item, str) and item.lower().startswith(prefix.lower()):
                    # Find the index of the item in the sublist
                    index = sublist.index(item)
                    # Check if there is a next item in the sublist
                    if index + 1 < len(sublist):
                        result = sublist[index + 1]
                        result = re.findall(r"[a-zA-Z]+|\d+|[^a-zA-Z\d\s]", result)

        if result:
            prefix = []
            incremented = False
            for item in reversed(result):
                total_letters = len(item)
                total_zero_leads = 0
                for letter in item:
                    if letter == "0":
                        total_zero_leads = total_zero_leads + 1
                        continue
                    break

                if total_zero_leads:
                    item = item[total_zero_leads:]
                if isinstance(item, list):
                    item = item[-1]
                if not incremented and isinstance(eval_validate(str(item)), int):
                    item = int(item) + 1
                    incremented = True
                if isinstance(item, int):
                    item = "{:0{}d}".format(item, total_letters)
                prefix.insert(0, str(item))
            prefix = "".join(prefix)
    except Exception as e:
        prefix = get_initial_prefix(None)["get_initial_prefix"]
    return prefix
