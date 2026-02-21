# WorkType Visibility Verification

## Answers to checklist

### 1. In WorkType table, does the newly created record have company_id assigned?

- **WorkType** uses a **ManyToManyField** for `company_id` (not a single FK). So there is no `company_id` column on `base_worktype`; the link is in the through table **`base_worktype_company_id`** (Django default: `{app}_{model}_{field}`).
- **Before the fix:** POST did not set `company_id`, so new rows had **no** related rows in `base_worktype_company_id`. So the created work type had **no company assigned**.
- **After the fix:** POST sets `data["company_id"] = [effective_company_id]` before `serializer.save()`, so the new WorkType gets a row in `base_worktype_company_id` and **does** have the employee’s company assigned.

**To confirm in DB:** Run the verification script (see below) or in Django shell:

```python
from base.models import WorkType
# Replace ID with the work type created by Dileesh
wt = WorkType.objects.get(id=YOUR_ID)
list(wt.company_id.values_list("id", flat=True))  # should be non-empty after fix
```

---

### 2. What does the GET work-type API return? Does it include the created work type?

- **Endpoint:** `GET /api/v1/base/worktypes/` (no pagination; returns a JSON array).
- **Behavior:** The list is filtered by **effective company**: `work_types.filter(company_id=effective_company_id)`. So the API returns only work types that have that company in their M2M `company_id`.
- **Before fix:** The new work type had no company in M2M → it was **not** included in the response.
- **After fix:** The new work type has the user’s company in M2M → it **is** included in the GET response.

**To confirm:** Call `GET /api/v1/base/worktypes/` with the same JWT as Dileesh (Employee). The created work type should appear in the JSON array after the fix.

---

### 3. Is the WorkType list API using company filter?

**Yes.** In `horilla_api/api_views/base/views.py`, `WorkTypeView.get()`:

```python
company_id = _get_effective_company_id(request)
work_types = WorkType.objects.all()
if company_id is not None:
    work_types = work_types.filter(company_id=company_id)
```

So the list uses **`filter(company_id=effective_company_id)`** when the user has an effective company (e.g. employee with a company).

---

### 4. In POST WorkTypeView, are we forcing `data["company_id"] = [effective_company_id]` before serializer.save()?

**Yes (after the fix).** In `WorkTypeView.post()`:

```python
data = request.data.copy()
company_id = _get_effective_company_id(request)
if company_id is not None:
    data["company_id"] = [company_id]
serializer = self.serializer_class(data=data)
if serializer.is_valid():
    serializer.save()
```

So we **do** set `data["company_id"] = [effective_company_id]` before validation/save when the user has an effective company.

---

### 5. Exact API URL used by React to fetch work types?

- **List (fetch work types):**  
  **`GET /api/v1/base/worktypes/`**

- **Detail:**  
  **`GET /api/v1/base/worktypes/<id>/`**

- **Create:**  
  **`POST /api/v1/base/worktypes/`**

Defined in Django: `horilla_api/api_urls/base/urls.py` → `path("worktypes/", ...)` under `path("base/", ...)`; main urlconf mounts at `path("api/v1/", include("horilla_api.urls"))` (see `horilla/urls.py`).

React uses these in `synchrm-ui/src/services/settings.service.js`:  
`getWorkTypes()` → `GET /api/v1/base/worktypes/`, `createWorkType()` → `POST /api/v1/base/worktypes/`.

---

## Quick verification script

From project root (with Django env):

```bash
cd a:\hrms\synchr
python manage.py shell
```

Then:

```python
exec(open('scripts/verify_worktype_company.py').read())
```

This prints:
1. Recent WorkType rows and their M2M `company_id` (ids and names).
2. Employee “Dileesh” and his company.
3. Work types that would be returned for that company (same as GET list filter).

If the work type created by Dileesh appears in (1) with his company in M2M and in (3), the backend is correct and the React list will show it after `loadData()`.
