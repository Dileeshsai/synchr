# WorkType API vs Frontend Mismatch – Check Report

## Request (copy-paste to agent)

```
Please check this mismatch:

Django Admin shows WorkTypes correctly,
but React frontend (GET /api/v1/base/worktypes/) does not match.

Kindly confirm:
1. What JSON is returned by GET /api/v1/base/worktypes/ when logged in as Dileesh?
2. Does the API response contain the newly created WorkType?
3. What is the effective_company_id resolved for Dileesh in _get_effective_company_id(request)?
4. Does the WorkType record in DB have company_id linked to the same company as Dileesh?
5. Is any additional filtering (is_active, archived, permission filter) applied in the queryset?
Please paste the raw API response JSON.
```

---

## Answers (from code + diagnostic script)

### 1. What JSON is returned by GET /api/v1/base/worktypes/ when logged in as Dileesh?

- **Endpoint:** `GET /api/v1/base/worktypes/` (no `pk`).
- **Logic:** `company_id = _get_effective_company_id(request)`. Then `work_types = WorkType.objects.all()`; if `company_id is not None`, then `work_types = work_types.filter(company_id=company_id)`. Serializer returns list of `{ "id", "work_type", "company_id": [list of company ids], ... }`.
- **Raw JSON shape:** Array of objects, e.g. `[{ "id": 1, "work_type": "On-site", "company_id": [2] }, ...]`.
- **To get your exact JSON:** Run the diagnostic script (see below) or call the API in browser while logged in as Dileesh: `http://localhost:8000/api/v1/base/worktypes/`.

### 2. Does the API response contain the newly created WorkType?

- **Only if** that WorkType’s **company_id (M2M)** includes the same company as **effective_company_id** for Dileesh.
- If the WorkType was created **after** the serializer fix, it should have `company_id = [effective_company_id]` and **will** appear.
- If the WorkType was created **before** the fix (or with no company), its M2M may be empty or different → it **will not** appear in the list for Dileesh.

### 3. What is the effective_company_id resolved for Dileesh?

- **Source:** `_get_effective_company_id(request)` in `horilla_api/api_views/base/views.py`.
- **Logic:**  
  - If query param `company_id` is sent and not `""` or `"all"` → use that.  
  - Else: `employee = request.user.employee_get`, then `company = employee.get_company()`.  
  - `get_company()` returns `employee.employee_work_info.company_id` (FK on EmployeeWorkInformation).
- **So for Dileesh:** `effective_company_id` = **Dileesh’s `employee_work_info.company_id`** (the company of his work info). If he has no `employee_work_info` or `company_id` is null, then `effective_company_id` is **None** and the list is **unfiltered** (all work types).

### 4. Does the WorkType record in DB have company_id linked to the same company as Dileesh?

- **WorkType** uses **ManyToMany** `company_id` (through table `base_worktype_company_id`).
- For a WorkType to show for Dileesh, that WorkType must have **at least one** row in `base_worktype_company_id` with `company_id` = Dileesh’s effective company id.
- **Check:** Run `scripts/diagnose_worktype_api.py` (see below); it prints each WorkType’s `company_ids` and whether they MATCH Dileesh’s company.

### 5. Is any additional filtering (is_active, archived, permission filter) applied in the queryset?

- **No.** The list view uses only:
  - `WorkType.objects.all()`
  - then, if `company_id is not None`, `.filter(company_id=company_id)`.
- WorkType model has **no** `is_active`, **no** `archived`, and **no** extra permission filter on the list queryset.

---

## How to get the raw API response JSON (you)

1. **Browser (with login):**  
   Log in as Dileesh in the same browser, then open:  
   `http://localhost:8000/api/v1/base/worktypes/`  
   You’ll see the exact JSON the frontend gets. If it’s `[]` → frontend will show empty.

2. **Diagnostic script (Django shell):**  
   From project root:
   ```bash
   cd A:\hrms\synchr
   python manage.py shell
   ```
   Then in the shell:
   ```python
   exec(open('scripts/diagnose_worktype_api.py').read())
   ```
   This prints:
   - effective_company_id for Dileesh
   - The same JSON the API would return for that company
   - For each WorkType in DB: company_ids and MATCH / NO MATCH vs Dileesh’s company

---

## Most likely root cause (90%)

- **Company mismatch:** WorkTypes in DB are linked to company A (or no company); Dileesh’s `effective_company_id` is company B. So the API correctly returns only work types for company B and they don’t include the ones you see in Admin (which shows all).
- **Fix:** Ensure when creating a WorkType (from API/React), backend sets `company_id = [effective_company_id]` (already done in POST). For **existing** WorkTypes created without company, either:
  - Re-save them in Admin and assign the correct company, or  
  - Run a one-off script to set `work_type.company_id.add(dileesh_company_id)` for those records.

---

## Your 3 short answers (for your contact)

1. **Django Admin lo WorkType company field lo emi value undi?**  
   → You check in Admin: open a WorkType, see “Company” (M2M). Note the company name(s).

2. **Top navbar lo organization name enti?**  
   → You check in React UI: e.g. “Tech Solutions Inc” or whatever is shown.

3. **Direct API open chesi check chesava?** `http://localhost:8000/api/v1/base/worktypes/`  
   → You open that URL while logged in as Dileesh and say: **EMPTY** or **HAS DATA**.

Once you have (1), (2), and (3), your contact can give the one-line permanent fix (e.g. “set company on existing WorkTypes” or “fix effective_company_id for this user”).
