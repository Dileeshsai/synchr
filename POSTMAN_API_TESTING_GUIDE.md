# Complete Postman API Testing Guide with Examples

**Base URL:** `http://127.0.0.1:8000/api/v1/`

---

## Setup Instructions

### 1. Create Postman Environment
Create a new environment with these variables:
- `base_url` = `http://127.0.0.1:8000/api/v1`
- `access_token` = (leave empty, will be set after login)

### 2. Login First (Get Token)
Before testing any other API, you must login to get the JWT token.

---

## 1. AUTHENTICATION APIs

### 1.1 Login
**POST** `{{base_url}}/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Example Response (200 OK):**
```json
{
  "employee": {
    "id": 1,
    "employee_first_name": "John",
    "employee_last_name": "Doe",
    "email": "john.doe@example.com"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "face_detection": false,
  "geo_fencing": false,
  "company_id": 1
}
```

**Postman Test Script (to auto-save token):**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access);
    console.log("Token saved:", jsonData.access);
}
```

---

### 1.2 Get User Profile
**GET** `{{base_url}}/auth/profile/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "id": 1,
  "employee_first_name": "John",
  "employee_last_name": "Doe",
  "email": "john.doe@example.com",
  "employee_profile": "/media/employee/profile/image.jpg"
}
```

---

### 1.3 Forgot Password
**POST** `{{base_url}}/auth/forgot-password/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "email": "user@example.com"
}
```

**Example Response (200 OK):**
```json
{
  "detail": "Password reset link sent to your email."
}
```

---

## 2. EMPLOYEE APIs

### 2.1 List All Employees
**GET** `{{base_url}}/employee/employees/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters (Optional):**
- `page` - Page number (default: 1)
- `page_size` - Items per page
- `search` - Search by name
- `groupby_field` - Group by field name

**Example Response (200 OK):**
```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/v1/employee/employees/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "employee_first_name": "John",
      "employee_last_name": "Doe",
      "email": "john.doe@example.com",
      "department_name": "IT",
      "job_position_name": "Software Developer",
      "employee_profile": "/media/employee/profile/image.jpg"
    }
  ]
}
```

---

### 2.2 Get Single Employee
**GET** `{{base_url}}/employee/employees/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "id": 1,
  "employee_first_name": "John",
  "employee_last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "department_name": "IT",
  "job_position_name": "Software Developer",
  "employee_work_info_id": 1,
  "employee_bank_details_id": 1
}
```

---

### 2.3 Create Employee
**POST** `{{base_url}}/employee/employees/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_first_name": "Jane",
  "employee_last_name": "Smith",
  "email": "jane.smith@example.com",
  "phone": "+1234567891",
  "badge_id": "EMP001"
}
```

**Example Response (201 Created):**
```json
{
  "id": 2,
  "employee_first_name": "Jane",
  "employee_last_name": "Smith",
  "email": "jane.smith@example.com",
  "phone": "+1234567891",
  "badge_id": "EMP001"
}
```

---

### 2.4 Update Employee
**PUT** `{{base_url}}/employee/employees/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_first_name": "John",
  "employee_last_name": "Doe Updated",
  "phone": "+1234567899"
}
```

**Example Response (200 OK):**
```json
{
  "id": 1,
  "employee_first_name": "John",
  "employee_last_name": "Doe Updated",
  "phone": "+1234567899"
}
```

---

### 2.5 Delete Employee
**DELETE** `{{base_url}}/employee/employees/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (204 No Content)**

---

### 2.6 Get Employee Bank Details
**GET** `{{base_url}}/employee/employee-bank-details/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "bank_name": "Chase Bank",
    "account_number": "1234567890",
    "ifsc_code": "CHAS123456"
  }
]
```

---

### 2.7 Create Employee Bank Details
**POST** `{{base_url}}/employee/employee-bank-details/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "bank_name": "Bank of America",
  "account_number": "9876543210",
  "ifsc_code": "BOFA987654",
  "branch": "New York Branch"
}
```

---

### 2.8 Get Employee Work Information
**GET** `{{base_url}}/employee/employee-work-information/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "job_position_id": 1,
    "job_position_name": "Software Developer",
    "department_id": 1,
    "reporting_manager_id": 2
  }
]
```

---

### 2.9 Create Employee Work Information
**POST** `{{base_url}}/employee/employee-work-information/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "job_position_id": 1,
  "department_id": 1,
  "reporting_manager_id": 2,
  "work_type_id": 1,
  "employee_shift_id": 1
}
```

---

### 2.10 Get Policies
**GET** `{{base_url}}/employee/policies/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Code of Conduct",
    "body": "Policy content here...",
    "is_active": true
  }
]
```

---

### 2.11 Create Policy
**POST** `{{base_url}}/employee/policies/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Remote Work Policy",
  "body": "Employees can work remotely 3 days per week...",
  "is_active": true
}
```

---

### 2.12 Get Documents
**GET** `{{base_url}}/employee/documents/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "document": "/media/documents/contract.pdf",
    "document_title": "Employment Contract"
  }
]
```

---

### 2.13 Get Employee Dashboard
**GET** `{{base_url}}/employee/dashboard/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "total_employees": 100,
  "active_employees": 95,
  "department_count": 10,
  "recent_activities": []
}
```

---

## 3. ATTENDANCE APIs

### 3.1 Clock In
**POST** `{{base_url}}/attendance/clock-in/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "attendance_date": "2024-01-15",
  "clock_in": "09:00:00",
  "work_type_id": 1
}
```

**Example Response (201 Created):**
```json
{
  "id": 1,
  "employee_id": 1,
  "attendance_date": "2024-01-15",
  "clock_in": "09:00:00",
  "attendance_validated": false
}
```

---

### 3.2 Clock Out
**POST** `{{base_url}}/attendance/clock-out/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "attendance_id": 1,
  "clock_out": "18:00:00"
}
```

**Example Response (200 OK):**
```json
{
  "id": 1,
  "employee_id": 1,
  "clock_in": "09:00:00",
  "clock_out": "18:00:00",
  "attendance_date": "2024-01-15"
}
```

---

### 3.3 List Attendance
**GET** `{{base_url}}/attendance/attendance/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `page` - Page number
- `employee_id` - Filter by employee
- `attendance_date` - Filter by date (YYYY-MM-DD)

**Example Response (200 OK):**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "employee_id": 1,
      "attendance_date": "2024-01-15",
      "clock_in": "09:00:00",
      "clock_out": "18:00:00",
      "attendance_validated": true
    }
  ]
}
```

---

### 3.4 Get Single Attendance
**GET** `{{base_url}}/attendance/attendance/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 3.5 Create Attendance Request
**POST** `{{base_url}}/attendance/attendance-request/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "attendance_date": "2024-01-16",
  "clock_in": "09:30:00",
  "clock_out": "18:30:00",
  "request_description": "Forgot to clock in"
}
```

---

### 3.6 Approve Attendance Request
**POST** `{{base_url}}/attendance/attendance-request-approve/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "message": "Attendance request approved successfully"
}
```

---

### 3.7 Get Today's Attendance
**GET** `{{base_url}}/attendance/today-attendance/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "employee_id": 1,
  "attendance_date": "2024-01-15",
  "clock_in": "09:00:00",
  "clock_out": null,
  "status": "checked_in"
}
```

---

### 3.8 Get Offline Employees Count
**GET** `{{base_url}}/attendance/offline-employees/count/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "offline_count": 5
}
```

---

## 4. LEAVE APIs

### 4.1 Get Available Leave Balance
**GET** `{{base_url}}/leave/available-leave/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `employee_id` - Employee ID (optional, defaults to logged-in user)

**Example Response (200 OK):**
```json
{
  "employee_id": 1,
  "leave_balances": [
    {
      "leave_type": "Annual Leave",
      "available_days": 15,
      "used_days": 5,
      "total_days": 20
    }
  ]
}
```

---

### 4.2 Create Leave Request
**POST** `{{base_url}}/leave/user-request/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "leave_type_id": 1,
  "start_date": "2024-02-01",
  "end_date": "2024-02-05",
  "reason": "Family vacation",
  "requested_days": 5
}
```

**Example Response (201 Created):**
```json
{
  "id": 1,
  "employee_id": 1,
  "leave_type_id": 1,
  "start_date": "2024-02-01",
  "end_date": "2024-02-05",
  "status": "requested",
  "requested_days": 5
}
```

---

### 4.3 List Leave Requests
**GET** `{{base_url}}/leave/leave-request/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `status` - Filter by status (requested, approved, rejected)
- `employee_id` - Filter by employee
- `page` - Page number

**Example Response (200 OK):**
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "employee_id": 1,
      "leave_type_id": 1,
      "start_date": "2024-02-01",
      "end_date": "2024-02-05",
      "status": "requested"
    }
  ]
}
```

---

### 4.4 Approve Leave Request
**POST** `{{base_url}}/leave/approve/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "comment": "Approved by manager"
}
```

**Example Response (200 OK):**
```json
{
  "message": "Leave request approved successfully",
  "leave_request_id": 1
}
```

---

### 4.5 Reject Leave Request
**POST** `{{base_url}}/leave/reject/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "comment": "Insufficient leave balance"
}
```

---

### 4.6 Get Leave Types
**GET** `{{base_url}}/leave/leave-types/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Annual Leave",
    "days": 20,
    "is_active": true
  },
  {
    "id": 2,
    "name": "Sick Leave",
    "days": 10,
    "is_active": true
  }
]
```

---

### 4.7 Create Leave Type
**POST** `{{base_url}}/leave/leave-types/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "name": "Personal Leave",
  "days": 5,
  "is_active": true,
  "reset_based": "yearly"
}
```

---

### 4.8 Get Holidays
**GET** `{{base_url}}/leave/holiday/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "New Year",
    "date": "2024-01-01",
    "recurring": true
  }
]
```

---

### 4.9 Create Holiday
**POST** `{{base_url}}/leave/holiday/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "name": "Independence Day",
  "date": "2024-07-04",
  "recurring": true
}
```

---

### 4.10 Get Leave Status Counts
**GET** `{{base_url}}/leave/status/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "requested": 5,
  "approved": 10,
  "rejected": 2,
  "cancelled": 1
}
```

---

## 5. PAYROLL APIs

### 5.1 List Contracts
**GET** `{{base_url}}/payroll/contract/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "wage_type": "monthly",
    "salary": 5000.00,
    "start_date": "2024-01-01",
    "end_date": null
  }
]
```

---

### 5.2 Create Contract
**POST** `{{base_url}}/payroll/contract/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "wage_type": "monthly",
  "salary": 5000.00,
  "start_date": "2024-01-01",
  "end_date": null
}
```

---

### 5.3 List Payslips
**GET** `{{base_url}}/payroll/payslip/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `employee_id` - Filter by employee
- `month` - Filter by month (YYYY-MM)
- `year` - Filter by year

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "month": "2024-01",
    "year": 2024,
    "basic_salary": 5000.00,
    "allowances": 500.00,
    "deductions": 200.00,
    "net_salary": 5300.00
  }
]
```

---

### 5.4 Get Single Payslip
**GET** `{{base_url}}/payroll/payslip/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 5.5 Download Payslip
**GET** `{{base_url}}/payroll/payslip-download/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Response:** PDF file download

---

### 5.6 Send Payslip via Email
**POST** `{{base_url}}/payroll/payslip-send-mail/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "payslip_id": 1,
  "email": "employee@example.com"
}
```

---

### 5.7 List Loan Accounts
**GET** `{{base_url}}/payroll/loan-account/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "loan_amount": 10000.00,
    "installment_amount": 1000.00,
    "remaining_amount": 5000.00,
    "status": "active"
  }
]
```

---

### 5.8 Create Loan Account
**POST** `{{base_url}}/payroll/loan-account/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "loan_amount": 10000.00,
  "installment_amount": 1000.00,
  "start_date": "2024-01-01",
  "end_date": "2024-10-01"
}
```

---

### 5.9 List Reimbursements
**GET** `{{base_url}}/payroll/reimbusement/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "title": "Travel Expense",
    "amount": 500.00,
    "date": "2024-01-10",
    "status": "pending"
  }
]
```

---

### 5.10 Create Reimbursement
**POST** `{{base_url}}/payroll/reimbusement/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "title": "Travel Expense",
  "amount": 500.00,
  "date": "2024-01-10",
  "description": "Client meeting travel",
  "attachment": "file_path_or_url"
}
```

---

### 5.11 Approve/Reject Reimbursement
**POST** `{{base_url}}/payroll/reimbusement-approve-reject/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "status": "approved",
  "comment": "Approved by finance"
}
```

---

### 5.12 List Allowances
**GET** `{{base_url}}/payroll/allowance`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Transport Allowance",
    "amount": 500.00,
    "is_taxable": true
  }
]
```

---

### 5.13 Create Allowance
**POST** `{{base_url}}/payroll/allowance`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Meal Allowance",
  "amount": 300.00,
  "is_taxable": false
}
```

---

### 5.14 List Deductions
**GET** `{{base_url}}/payroll/deduction`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 5.15 Get All Payroll Records
**GET** `{{base_url}}/payroll/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

## 6. ASSET APIs

### 6.1 List Assets
**GET** `{{base_url}}/asset/assets/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "asset_name": "Laptop Dell XPS",
    "asset_category_id": 1,
    "asset_lot_id": 1,
    "status": "available",
    "purchase_date": "2024-01-01",
    "purchase_cost": 1200.00
  }
]
```

---

### 6.2 Create Asset
**POST** `{{base_url}}/asset/assets/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "asset_name": "MacBook Pro",
  "asset_category_id": 1,
  "asset_lot_id": 1,
  "purchase_date": "2024-01-15",
  "purchase_cost": 2000.00,
  "status": "available"
}
```

---

### 6.3 List Asset Categories
**GET** `{{base_url}}/asset/asset-categories/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "asset_category_name": "Electronics",
    "description": "Electronic devices"
  }
]
```

---

### 6.4 Create Asset Category
**POST** `{{base_url}}/asset/asset-categories/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "asset_category_name": "Furniture",
  "description": "Office furniture and equipment"
}
```

---

### 6.5 List Asset Allocations
**GET** `{{base_url}}/asset/asset-allocations/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "asset_id": 1,
    "employee_id": 1,
    "allocated_date": "2024-01-10",
    "return_date": null,
    "status": "allocated"
  }
]
```

---

### 6.6 Create Asset Allocation
**POST** `{{base_url}}/asset/asset-allocations/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "asset_id": 1,
  "employee_id": 1,
  "allocated_date": "2024-01-10",
  "allocation_description": "Assigned for work"
}
```

---

### 6.7 List Asset Requests
**GET** `{{base_url}}/asset/asset-requests/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 6.8 Create Asset Request
**POST** `{{base_url}}/asset/asset-requests/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "asset_id": 1,
  "employee_id": 1,
  "request_description": "Need laptop for remote work"
}
```

---

### 6.9 Approve Asset Request
**POST** `{{base_url}}/asset/asset-approve/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 6.10 Reject Asset Request
**POST** `{{base_url}}/asset/asset-reject/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 6.11 Return Asset
**POST** `{{base_url}}/asset/asset-return/1`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "return_date": "2024-01-20",
  "return_condition": "Good",
  "return_description": "Returned in good condition"
}
```

---

## 7. BASE/ORGANIZATION APIs

### 7.1 List Companies
**GET** `{{base_url}}/base/companies/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "company": "Acme Corporation",
    "address": "123 Main St",
    "country": "USA",
    "is_active": true
  }
]
```

---

### 7.2 Create Company
**POST** `{{base_url}}/base/companies/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "company": "New Company Inc",
  "address": "456 Business Ave",
  "country": "USA",
  "phone": "+1234567890",
  "email": "info@newcompany.com"
}
```

---

### 7.3 List Departments
**GET** `{{base_url}}/base/departments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "department": "IT",
    "company_id": 1,
    "is_active": true
  }
]
```

---

### 7.4 Create Department
**POST** `{{base_url}}/base/departments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "department": "Human Resources",
  "company_id": 1
}
```

---

### 7.5 List Job Positions
**GET** `{{base_url}}/base/job-positions/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "job_position": "Software Developer",
    "department_id": 1,
    "is_active": true
  }
]
```

---

### 7.6 Create Job Position
**POST** `{{base_url}}/base/job-positions/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "job_position": "Senior Developer",
  "department_id": 1,
  "description": "Senior software development role"
}
```

---

### 7.7 List Job Roles
**GET** `{{base_url}}/base/job-roles/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 7.8 List Work Types
**GET** `{{base_url}}/base/worktypes/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "work_type": "Remote",
    "is_active": true
  },
  {
    "id": 2,
    "work_type": "Office",
    "is_active": true
  }
]
```

---

### 7.9 List Employee Shifts
**GET** `{{base_url}}/base/employee-shift/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_shift": "Morning Shift",
    "start_time": "09:00:00",
    "end_time": "18:00:00"
  }
]
```

---

### 7.10 Create Employee Shift
**POST** `{{base_url}}/base/employee-shift/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_shift": "Night Shift",
  "start_time": "22:00:00",
  "end_time": "06:00:00"
}
```

---

## 8. NOTIFICATIONS APIs

### 8.1 List Notifications
**GET** `{{base_url}}/notifications/notifications/list/all`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `type` - Notification type (all, unread, read)

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "verb": "Leave request approved",
    "description": "Your leave request has been approved",
    "unread": true,
    "timestamp": "2024-01-15T10:30:00Z"
  }
]
```

---

### 8.2 Get Single Notification
**GET** `{{base_url}}/notifications/notifications/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 8.3 Delete Notification
**DELETE** `{{base_url}}/notifications/notifications/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 8.4 Bulk Mark as Read
**POST** `{{base_url}}/notifications/notifications/bulk-read/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "notification_ids": [1, 2, 3]
}
```

---

### 8.5 Bulk Delete
**POST** `{{base_url}}/notifications/notifications/bulk-delete/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "notification_ids": [1, 2, 3]
}
```

---

## 9. FACE DETECTION APIs

### 9.1 Get Face Detection Config
**GET** `{{base_url}}/facedetection/config/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "face_detection_enabled": true,
  "tolerance": 0.6,
  "company_id": 1
}
```

---

### 9.2 Update Face Detection Config
**POST** `{{base_url}}/facedetection/config/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "face_detection_enabled": true,
  "tolerance": 0.6
}
```

---

### 9.3 List Employee Face Records
**GET** `{{base_url}}/facedetection/employees/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 9.4 Register Employee Face
**POST** `{{base_url}}/facedetection/employees/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: multipart/form-data
```

**Body (form-data):**
- `employee_id`: 1
- `image`: [Select File]

---

### 9.5 Verify Face
**POST** `{{base_url}}/facedetection/verify/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: multipart/form-data
```

**Body (form-data):**
- `image`: [Select File]
- `employee_id`: 1 (optional)

---

### 9.6 Face Check-in
**POST** `{{base_url}}/facedetection/checkin/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: multipart/form-data
```

**Body (form-data):**
- `image`: [Select File]
- `employee_id`: 1

---

### 9.7 Face Check-out
**POST** `{{base_url}}/facedetection/checkout/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: multipart/form-data
```

**Body (form-data):**
- `image`: [Select File]
- `employee_id`: 1

---

### 9.8 Get Face Detection Status
**GET** `{{base_url}}/facedetection/status/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 9.9 Get Face Recognition Stats
**GET** `{{base_url}}/facedetection/stats/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

## 10. RECRUITMENT APIs (NEW)

### 10.1 List Recruitments
**GET** `{{base_url}}/recruitment/recruitments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "title": "Software Developer Position",
      "description": "Looking for experienced developer",
      "job_position_id": 1,
      "job_position_name": "Software Developer",
      "vacancy": 3,
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "is_published": true,
      "closed": false
    }
  ]
}
```

---

### 10.2 Create Recruitment
**POST** `{{base_url}}/recruitment/recruitments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Senior Developer Position",
  "description": "Looking for senior developer with 5+ years experience",
  "job_position_id": 1,
  "vacancy": 2,
  "start_date": "2024-02-01",
  "end_date": "2024-04-30",
  "is_published": true
}
```

---

### 10.3 List Candidates
**GET** `{{base_url}}/recruitment/candidates/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "name": "John Candidate",
      "email": "john.candidate@example.com",
      "mobile": "+1234567890",
      "recruitment_id": 1,
      "recruitment_title": "Software Developer Position",
      "stage_id": 1,
      "stage_title": "Initial Screening"
    }
  ]
}
```

---

### 10.4 Create Candidate
**POST** `{{base_url}}/recruitment/candidates/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "name": "Jane Candidate",
  "email": "jane.candidate@example.com",
  "mobile": "+1234567891",
  "recruitment_id": 1,
  "stage_id": 1,
  "profile": "file_path_or_url"
}
```

---

### 10.5 List Stages
**GET** `{{base_url}}/recruitment/stages/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "recruitment_id": 1,
    "recruitment_title": "Software Developer Position",
    "stage": "Initial Screening",
    "sequence": 1,
    "is_active": true
  }
]
```

---

### 10.6 Create Stage
**POST** `{{base_url}}/recruitment/stages/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "recruitment_id": 1,
  "stage": "Technical Interview",
  "sequence": 2,
  "is_active": true
}
```

---

### 10.7 List Interviews
**GET** `{{base_url}}/recruitment/interviews/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "candidate_id": 1,
    "candidate_name": "John Candidate",
    "employee_id": 2,
    "employee_name": "Interviewer Name",
    "interview_date": "2024-02-15",
    "interview_time": "14:00:00",
    "interview_mode": "online"
  }
]
```

---

### 10.8 Create Interview Schedule
**POST** `{{base_url}}/recruitment/interviews/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "candidate_id": 1,
  "employee_id": 2,
  "interview_date": "2024-02-15",
  "interview_time": "14:00:00",
  "interview_mode": "online",
  "interview_link": "https://meet.example.com/interview"
}
```

---

### 10.9 List Skills
**GET** `{{base_url}}/recruitment/skills/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Python"
  },
  {
    "id": 2,
    "title": "Django"
  }
]
```

---

### 10.10 Create Skill
**POST** `{{base_url}}/recruitment/skills/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "React"
}
```

---

## 11. PMS APIs (NEW)

### 11.1 List Periods
**GET** `{{base_url}}/pms/periods/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "period_name": "Q1 2024",
    "start_date": "2024-01-01",
    "end_date": "2024-03-31"
  }
]
```

---

### 11.2 Create Period
**POST** `{{base_url}}/pms/periods/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "period_name": "Q2 2024",
  "start_date": "2024-04-01",
  "end_date": "2024-06-30"
}
```

---

### 11.3 List Objectives
**GET** `{{base_url}}/pms/objectives/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Increase Sales",
    "description": "Increase sales by 20%",
    "duration": 90,
    "duration_unit": "days",
    "company_name": "Acme Corporation"
  }
]
```

---

### 11.4 Create Objective
**POST** `{{base_url}}/pms/objectives/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Improve Customer Satisfaction",
  "description": "Achieve 95% customer satisfaction rating",
  "duration": 60,
  "duration_unit": "days",
  "managers": [1, 2],
  "assignees": [3, 4]
}
```

---

### 11.5 List Employee Objectives
**GET** `{{base_url}}/pms/employee-objectives/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "John Doe",
    "objective_id": 1,
    "objective_title": "Increase Sales",
    "status": "On Track",
    "progress": 65
  }
]
```

---

### 11.6 Create Employee Objective
**POST** `{{base_url}}/pms/employee-objectives/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "objective_id": 1,
  "status": "On Track",
  "progress": 0
}
```

---

### 11.7 List Key Results
**GET** `{{base_url}}/pms/key-results/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 11.8 List Feedback
**GET** `{{base_url}}/pms/feedback/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "John Doe",
    "review_cycle_name": "Q1 2024",
    "feedback_type": "peer",
    "status": "completed"
  }
]
```

---

### 11.9 Create Feedback
**POST** `{{base_url}}/pms/feedback/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "review_cycle_id": 1,
  "feedback_type": "peer",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

---

### 11.10 List Meetings
**GET** `{{base_url}}/pms/meetings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 11.11 Create Meeting
**POST** `{{base_url}}/pms/meetings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "title": "Performance Review Meeting",
  "meeting_date": "2024-02-01",
  "meeting_time": "14:00:00",
  "meeting_link": "https://meet.example.com/review"
}
```

---

## 12. ONBOARDING APIs (NEW)

### 12.1 List Onboarding Stages
**GET** `{{base_url}}/onboarding/stages/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "recruitment_id": 1,
    "recruitment_title": "Software Developer Position",
    "stage_title": "Documentation",
    "sequence": 1,
    "is_final_stage": false
  }
]
```

---

### 12.2 Create Onboarding Stage
**POST** `{{base_url}}/onboarding/stages/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "recruitment_id": 1,
  "stage_title": "Orientation",
  "sequence": 2,
  "is_final_stage": false,
  "employee_id": [1, 2]
}
```

---

### 12.3 List Onboarding Tasks
**GET** `{{base_url}}/onboarding/tasks/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 12.4 Create Onboarding Task
**POST** `{{base_url}}/onboarding/tasks/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "stage_id": 1,
  "task_title": "Complete Documentation",
  "employee_id": [1],
  "candidates": [1]
}
```

---

### 12.5 List Candidate Stages
**GET** `{{base_url}}/onboarding/candidate-stages/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 12.6 List Candidate Tasks
**GET** `{{base_url}}/onboarding/candidate-tasks/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "candidate_id": 1,
    "candidate_name": "John Candidate",
    "onboarding_task_id": 1,
    "task_title": "Complete Documentation",
    "status": "todo",
    "stage_id": 1,
    "stage_title": "Documentation"
  }
]
```

---

## 13. OFFBOARDING APIs (NEW)

### 13.1 List Offboardings
**GET** `{{base_url}}/offboarding/offboardings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Standard Offboarding Process",
    "description": "Standard process for employee offboarding",
    "status": "ongoing",
    "company_name": "Acme Corporation"
  }
]
```

---

### 13.2 Create Offboarding
**POST** `{{base_url}}/offboarding/offboardings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Executive Offboarding",
  "description": "Offboarding process for executives",
  "status": "ongoing",
  "managers": [1, 2]
}
```

---

### 13.3 List Resignation Letters
**GET** `{{base_url}}/offboarding/resignation-letters/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "John Doe",
    "title": "Resignation Letter",
    "description": "I am resigning from my position...",
    "planned_to_leave_on": "2024-03-01",
    "status": "requested"
  }
]
```

---

### 13.4 Create Resignation Letter
**POST** `{{base_url}}/offboarding/resignation-letters/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "employee_id": 1,
  "title": "Resignation Letter",
  "description": "I am resigning from my position effective March 1, 2024",
  "planned_to_leave_on": "2024-03-01"
}
```

---

### 13.5 List Offboarding Employees
**GET** `{{base_url}}/offboarding/employees/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 13.6 List Employee Tasks
**GET** `{{base_url}}/offboarding/employee-tasks/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "John Doe",
    "task_id": 1,
    "task_title": "Return Laptop",
    "status": "todo",
    "description": "Return company laptop"
  }
]
```

---

## 14. HELPDESK APIs (NEW)

### 14.1 List Tickets
**GET** `{{base_url}}/helpdesk/tickets/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "title": "Laptop not working",
      "employee_id": 1,
      "employee_name": "John Doe",
      "ticket_type": 1,
      "ticket_type_title": "Service Request",
      "description": "My laptop is not turning on",
      "priority": "high",
      "status": "in_progress",
      "created_date": "2024-01-15"
    }
  ]
}
```

---

### 14.2 Create Ticket
**POST** `{{base_url}}/helpdesk/tickets/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Need Software License",
  "employee_id": 1,
  "ticket_type": 1,
  "description": "I need a license for Adobe Photoshop",
  "priority": "medium",
  "assigning_type": "department",
  "raised_on": "1",
  "deadline": "2024-02-01"
}
```

---

### 14.3 Update Ticket Status
**PUT** `{{base_url}}/helpdesk/tickets/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "status": "resolved",
  "resolved_date": "2024-01-20"
}
```

---

### 14.4 List Ticket Types
**GET** `{{base_url}}/helpdesk/ticket-types/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

### 14.5 Create Ticket Type
**POST** `{{base_url}}/helpdesk/ticket-types/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Hardware Issue",
  "type": "service_request",
  "prefix": "HW"
}
```

---

### 14.6 List Comments
**GET** `{{base_url}}/helpdesk/comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `ticket` - Filter by ticket ID

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "ticket": 1,
    "ticket_title": "Laptop not working",
    "employee_id": 1,
    "employee_name": "John Doe",
    "comment": "I've checked the laptop, it needs repair",
    "date": "2024-01-16T10:30:00Z"
  }
]
```

---

### 14.7 Create Comment
**POST** `{{base_url}}/helpdesk/comments/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "ticket": 1,
  "employee_id": 1,
  "comment": "The issue has been resolved. Laptop is working now."
}
```

---

### 14.8 List FAQs
**GET** `{{base_url}}/helpdesk/faqs/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "question": "How do I reset my password?",
    "answer": "Click on forgot password link on login page",
    "category": 1,
    "category_title": "Account Management"
  }
]
```

---

### 14.9 Create FAQ
**POST** `{{base_url}}/helpdesk/faqs/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "question": "How to request leave?",
  "answer": "Go to Leave module and click on Request Leave",
  "category": 1,
  "tags": [1, 2]
}
```

---

### 14.10 List FAQ Categories
**GET** `{{base_url}}/helpdesk/faq-categories/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

---

## 15. PROJECT APIs (NEW)

### 15.1 List Projects
**GET** `{{base_url}}/project/projects/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "title": "Website Redesign",
      "description": "Redesign company website",
      "status": "in_progress",
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "company_name": "Acme Corporation"
    }
  ]
}
```

---

### 15.2 Create Project
**POST** `{{base_url}}/project/projects/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Mobile App Development",
  "description": "Develop mobile app for iOS and Android",
  "status": "new",
  "start_date": "2024-02-01",
  "end_date": "2024-06-30",
  "managers": [1, 2],
  "members": [3, 4, 5]
}
```

---

### 15.3 List Tasks
**GET** `{{base_url}}/project/tasks/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `project` - Filter by project ID
- `status` - Filter by status (to_do, in_progress, completed)

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "project": 1,
    "project_title": "Website Redesign",
    "stage": 1,
    "stage_title": "Todo",
    "title": "Design Homepage",
    "status": "in_progress",
    "start_date": "2024-01-15",
    "end_date": "2024-01-30"
  }
]
```

---

### 15.4 Create Task
**POST** `{{base_url}}/project/tasks/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "project": 1,
  "stage": 1,
  "title": "Create Login Page",
  "description": "Design and implement login functionality",
  "status": "to_do",
  "start_date": "2024-02-01",
  "end_date": "2024-02-15",
  "task_managers": [1],
  "task_members": [2, 3]
}
```

---

### 15.5 List Timesheets
**GET** `{{base_url}}/project/timesheets/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `project_id` - Filter by project
- `task_id` - Filter by task
- `employee_id` - Filter by employee
- `date` - Filter by date

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "project_id": 1,
    "project_title": "Website Redesign",
    "task_id": 1,
    "task_title": "Design Homepage",
    "employee_id": 1,
    "employee_name": "John Doe",
    "date": "2024-01-15",
    "time_spent": "08:00",
    "status": "completed",
    "description": "Worked on homepage design"
  }
]
```

---

### 15.6 Create Timesheet
**POST** `{{base_url}}/project/timesheets/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "project_id": 1,
  "task_id": 1,
  "employee_id": 1,
  "date": "2024-01-16",
  "time_spent": "06:30",
  "status": "in_Progress",
  "description": "Implemented login functionality"
}
```

---

## 16. GEOFENCING APIs (NEW)

### 16.1 List Geofencing Configurations
**GET** `{{base_url}}/geofencing/geofencings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Example Response (200 OK):**
```json
[
  {
    "id": 1,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_in_meters": 100,
    "company_id": 1,
    "company_name": "Acme Corporation",
    "start": true
  }
]
```

---

### 16.2 Create Geofencing Configuration
**POST** `{{base_url}}/geofencing/geofencings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "radius_in_meters": 150,
  "company_id": 1,
  "start": true
}
```

---

### 16.3 Update Geofencing Configuration
**PUT** `{{base_url}}/geofencing/geofencings/1/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "radius_in_meters": 200,
  "start": false
}
```

---

## POSTMAN COLLECTION SETUP

### Step 1: Create Environment
1. Click on "Environments" in Postman
2. Click "Create Environment"
3. Name it "Sync HRMS"
4. Add variables:
   - `base_url` = `http://127.0.0.1:8000/api/v1`
   - `access_token` = (leave empty)

### Step 2: Create Collection
1. Click "New" → "Collection"
2. Name it "Sync HRMS APIs"
3. Go to "Authorization" tab
4. Type: Bearer Token
5. Token: `{{access_token}}`

### Step 3: Create Folders
Create folders for each module:
- 01 Authentication
- 02 Employee
- 03 Attendance
- 04 Leave
- 05 Payroll
- 06 Asset
- 07 Base
- 08 Notifications
- 09 Face Detection
- 10 Recruitment
- 11 PMS
- 12 Onboarding
- 13 Offboarding
- 14 Helpdesk
- 15 Project
- 16 Geofencing

### Step 4: Add Login Request
1. Create request in "01 Authentication" folder
2. Name: "Login"
3. Method: POST
4. URL: `{{base_url}}/auth/login/`
5. Body → raw → JSON:
```json
{
  "username": "admin",
  "password": "your_password"
}
```
6. Tests tab → Add script:
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access);
    console.log("Token saved:", jsonData.access);
}
```

### Step 5: Test Other APIs
All other requests will automatically use the token from the environment.

---

## COMMON ERROR RESPONSES

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Solution:** Make sure you're logged in and token is set.

### 400 Bad Request
```json
{
  "field_name": ["This field is required."]
}
```
**Solution:** Check request body and include all required fields.

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```
**Solution:** Check if the ID exists in the database.

### 403 Forbidden
```json
{
  "error": "You don't have permission"
}
```
**Solution:** Check user permissions for the action.

---

## TIPS FOR TESTING

1. **Always login first** - Get token before testing other APIs
2. **Check response status** - 200/201 = Success, 400 = Bad Request, 401 = Unauthorized
3. **Use pagination** - For list endpoints, use `?page=1&page_size=10`
4. **Filter results** - Use query parameters to filter data
5. **Save responses** - Use Postman's "Save Response" feature for reference
6. **Test error cases** - Try invalid data to see error handling
7. **Check relationships** - When creating records, ensure related IDs exist

---

## QUICK TEST CHECKLIST

- [ ] Login and get token
- [ ] Get user profile
- [ ] List employees
- [ ] Create employee
- [ ] Clock in/out
- [ ] Create leave request
- [ ] List projects
- [ ] Create ticket
- [ ] List recruitments
- [ ] Create candidate

---

**Total Endpoints: 200+ APIs ready for testing!**

