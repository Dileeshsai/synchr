# Complete API Endpoints Reference for Sync HRMS

**Base URL:** `http://127.0.0.1:8000/api/v1/`

**Authentication:** JWT Token (get from `/api/v1/auth/login/`)
- Use in Header: `Authorization: Bearer <token>`

---

## 1. Authentication APIs (`/api/v1/auth/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | Login and get JWT token |
| POST | `/api/v1/auth/forgot-password/` | Request password reset |
| GET | `/api/v1/auth/profile/` | Get user profile (requires auth) |

**Login Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

---

## 2. Employee APIs (`/api/v1/employee/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/employee/employees/` | List/Create employees |
| GET, PUT, DELETE | `/api/v1/employee/employees/<id>/` | Get/Update/Delete employee |
| GET, POST | `/api/v1/employee/employee-type/` | List/Create employee types |
| GET, PUT, DELETE | `/api/v1/employee/employee-type/<id>/` | Get/Update/Delete employee type |
| GET | `/api/v1/employee/list/employees/` | Detailed employee list |
| GET, POST | `/api/v1/employee/employee-bank-details/` | List/Create bank details |
| GET, PUT, DELETE | `/api/v1/employee/employee-bank-details/<id>/` | Get/Update/Delete bank details |
| GET, POST | `/api/v1/employee/employee-work-information/` | List/Create work info |
| GET, PUT, DELETE | `/api/v1/employee/employee-work-information/<id>/` | Get/Update/Delete work info |
| POST | `/api/v1/employee/employee-work-info-export/` | Export work info |
| POST | `/api/v1/employee/employee-work-info-import/` | Import work info |
| POST | `/api/v1/employee/employee-bulk-update/` | Bulk update employees |
| GET, POST | `/api/v1/employee/disciplinary-action/` | List/Create disciplinary actions |
| GET, PUT, DELETE | `/api/v1/employee/disciplinary-action/<id>/` | Get/Update/Delete disciplinary action |
| GET, POST | `/api/v1/employee/disciplinary-action-type/` | List/Create action types |
| GET, PUT, DELETE | `/api/v1/employee/disciplinary-action-type/<id>/` | Get/Update/Delete action type |
| GET, POST | `/api/v1/employee/policies/` | List/Create policies |
| GET, PUT, DELETE | `/api/v1/employee/policies/<id>/` | Get/Update/Delete policy |
| GET, POST | `/api/v1/employee/document-request/` | List/Create document requests |
| GET, PUT, DELETE | `/api/v1/employee/document-request/<id>/` | Get/Update/Delete document request |
| POST | `/api/v1/employee/document-bulk-approve-reject/` | Bulk approve/reject documents |
| POST | `/api/v1/employee/document-request-approve-reject/<id>/<status>/` | Approve/Reject document |
| GET, POST | `/api/v1/employee/documents/` | List/Create documents |
| GET, PUT, DELETE | `/api/v1/employee/documents/<id>/` | Get/Update/Delete document |
| POST | `/api/v1/employee/employee-bulk-archive/<is_active>/` | Bulk archive employees |
| POST | `/api/v1/employee/employee-archive/<id>/<is_active>/` | Archive/Unarchive employee |
| GET | `/api/v1/employee/employee-selector/` | Get employee selector |
| GET | `/api/v1/employee/manager-check/` | Check reporting manager |
| GET | `/api/v1/employee/dashboard/` | Employee dashboard data |
| GET | `/api/v1/employee/role-based-list/` | Role-based employee list |

---

## 3. Attendance APIs (`/api/v1/attendance/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/attendance/clock-in/` | Clock in |
| POST | `/api/v1/attendance/clock-out/` | Clock out |
| GET, POST | `/api/v1/attendance/attendance/` | List/Create attendance |
| GET, PUT, DELETE | `/api/v1/attendance/attendance/<id>` | Get/Update/Delete attendance |
| GET | `/api/v1/attendance/attendance/list/<type>` | List attendance by type |
| POST | `/api/v1/attendance/attendance-validate/<id>` | Validate attendance |
| GET, POST | `/api/v1/attendance/attendance-request/` | List/Create attendance requests |
| GET, PUT, DELETE | `/api/v1/attendance/attendance-request/<id>` | Get/Update/Delete request |
| POST | `/api/v1/attendance/attendance-request-approve/<id>` | Approve attendance request |
| POST | `/api/v1/attendance/attendance-request-cancel/<id>` | Cancel attendance request |
| POST | `/api/v1/attendance/overtime-approve/<id>` | Approve overtime |
| GET, POST | `/api/v1/attendance/attendance-hour-account/` | List/Create hour accounts |
| GET, PUT, DELETE | `/api/v1/attendance/attendance-hour-account/<id>/` | Get/Update/Delete hour account |
| GET, POST | `/api/v1/attendance/late-come-early-out-view/` | List/Create late/early records |
| GET, PUT, DELETE | `/api/v1/attendance/late-come-early-out-view/<id>/` | Get/Update/Delete record |
| GET | `/api/v1/attendance/attendance-activity/` | Get attendance activities |
| GET | `/api/v1/attendance/today-attendance/` | Get today's attendance |
| GET | `/api/v1/attendance/offline-employees/count/` | Count offline employees |
| GET | `/api/v1/attendance/offline-employees/list/` | List offline employees |
| GET | `/api/v1/attendance/permission-check/attendance` | Check attendance permissions |
| GET | `/api/v1/attendance/checking-in` | Check clock-in status |
| GET | `/api/v1/attendance/checking-out` | Check clock-out status |
| POST | `/api/v1/attendance/offline-employee-mail-send` | Send mail to offline employees |
| POST | `/api/v1/attendance/converted-mail-template` | Convert mail template |
| GET, POST | `/api/v1/attendance/mail-templates` | List/Create mail templates |

---

## 4. Leave APIs (`/api/v1/leave/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/leave/` | All leave details |
| GET | `/api/v1/leave/available-leave/` | Get available leave balance |
| GET, POST | `/api/v1/leave/user-request/` | List/Create user leave requests |
| GET, PUT, DELETE | `/api/v1/leave/user-request/<id>/` | Get/Update/Delete user request |
| GET, POST | `/api/v1/leave/leave-types/` | List/Create leave types |
| GET, PUT, DELETE | `/api/v1/leave/leave-types/<id>/` | Get/Update/Delete leave type |
| GET, POST | `/api/v1/leave/allocation-request/` | List/Create allocation requests |
| GET, PUT, DELETE | `/api/v1/leave/allocation-request/<id>/` | Get/Update/Delete allocation request |
| GET, POST | `/api/v1/leave/assign-leave/` | List/Create assigned leaves |
| GET, PUT, DELETE | `/api/v1/leave/assign-leave/<id>/` | Get/Update/Delete assigned leave |
| GET, POST | `/api/v1/leave/leave-request/` | List/Create leave requests |
| GET, PUT, DELETE | `/api/v1/leave/leave-request/<id>/` | Get/Update/Delete leave request |
| GET, POST | `/api/v1/leave/company-leave/` | List/Create company leaves |
| GET, PUT, DELETE | `/api/v1/leave/company-leave/<id>/` | Get/Update/Delete company leave |
| GET, POST | `/api/v1/leave/holiday/` | List/Create holidays |
| GET, PUT, DELETE | `/api/v1/leave/holiday/<id>/` | Get/Update/Delete holiday |
| POST | `/api/v1/leave/approve/<id>/` | Approve leave request |
| POST | `/api/v1/leave/reject/<id>/` | Reject leave request |
| POST | `/api/v1/leave/cancel/<id>/` | Cancel leave request |
| POST | `/api/v1/leave/allocation-approve/<id>/` | Approve allocation request |
| POST | `/api/v1/leave/allocation-reject/<id>/` | Reject allocation request |
| POST | `/api/v1/leave/request-bulk-action/` | Bulk approve/delete requests |
| GET, POST | `/api/v1/leave/user-allocation-request/` | List/Create user allocation requests |
| GET, PUT, DELETE | `/api/v1/leave/user-allocation-request/<id>/` | Get/Update/Delete user allocation |
| GET | `/api/v1/leave/status/` | Get leave request status counts |
| GET | `/api/v1/leave/employee-leave-type/<id>/` | Get employee leave types |
| GET | `/api/v1/leave/check-type/` | Check leave type permissions |
| GET | `/api/v1/leave/check-allocation/` | Check allocation permissions |
| GET | `/api/v1/leave/check-request/` | Check request permissions |
| GET | `/api/v1/leave/check-assign/` | Check assign permissions |
| GET | `/api/v1/leave/check-perm/` | Check all leave permissions |

---

## 5. Payroll APIs (`/api/v1/payroll/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/payroll/contract/` | List/Create contracts |
| GET, PUT, DELETE | `/api/v1/payroll/contract/<id>` | Get/Update/Delete contract |
| GET, POST | `/api/v1/payroll/payslip/` | List/Create payslips |
| GET | `/api/v1/payroll/payslip/<id>` | Get payslip details |
| GET | `/api/v1/payroll/payslip-download/<id>` | Download payslip |
| POST | `/api/v1/payroll/payslip-send-mail/` | Send payslip via email |
| GET, POST | `/api/v1/payroll/loan-account/` | List/Create loan accounts |
| GET, PUT, DELETE | `/api/v1/payroll/loan-account/<id>` | Get/Update/Delete loan account |
| GET, POST | `/api/v1/payroll/reimbusement/` | List/Create reimbursements |
| GET, PUT, DELETE | `/api/v1/payroll/reimbusement/<id>` | Get/Update/Delete reimbursement |
| POST | `/api/v1/payroll/reimbusement-approve-reject/<id>` | Approve/Reject reimbursement |
| GET, POST | `/api/v1/payroll/tax-bracket/` | List/Create tax brackets |
| GET, PUT, DELETE | `/api/v1/payroll/tax-bracket/<id>` | Get/Update/Delete tax bracket |
| GET, POST | `/api/v1/payroll/allowance` | List/Create allowances |
| GET, PUT, DELETE | `/api/v1/payroll/allowance/<id>` | Get/Update/Delete allowance |
| GET, POST | `/api/v1/payroll/deduction` | List/Create deductions |
| GET, PUT, DELETE | `/api/v1/payroll/deduction/<id>` | Get/Update/Delete deduction |
| GET | `/api/v1/payroll/` | Get all payroll records |

---

## 6. Asset APIs (`/api/v1/asset/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/asset/asset-categories/` | List/Create asset categories |
| GET, PUT, DELETE | `/api/v1/asset/asset-categories/<id>` | Get/Update/Delete category |
| GET, POST | `/api/v1/asset/asset-lots/` | List/Create asset lots |
| GET, PUT, DELETE | `/api/v1/asset/asset-lots/<id>` | Get/Update/Delete lot |
| GET, POST | `/api/v1/asset/assets/` | List/Create assets |
| GET, PUT, DELETE | `/api/v1/asset/assets/<id>` | Get/Update/Delete asset |
| GET, POST | `/api/v1/asset/asset-allocations/` | List/Create allocations |
| GET, PUT, DELETE | `/api/v1/asset/asset-allocations/<id>` | Get/Update/Delete allocation |
| GET, POST | `/api/v1/asset/asset-requests/` | List/Create asset requests |
| GET, PUT, DELETE | `/api/v1/asset/asset-requests/<id>` | Get/Update/Delete request |
| POST | `/api/v1/asset/asset-return/<id>` | Return asset |
| POST | `/api/v1/asset/asset-reject/<id>` | Reject asset request |
| POST | `/api/v1/asset/asset-approve/<id>` | Approve asset request |

---

## 7. Base/Organization APIs (`/api/v1/base/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/base/job-positions/` | List/Create job positions |
| GET, PUT, DELETE | `/api/v1/base/job-positions/<id>/` | Get/Update/Delete position |
| GET, POST | `/api/v1/base/job-roles/` | List/Create job roles |
| GET, PUT, DELETE | `/api/v1/base/job-roles/<id>/` | Get/Update/Delete role |
| GET, POST | `/api/v1/base/companies/` | List/Create companies |
| GET, PUT, DELETE | `/api/v1/base/companies/<id>/` | Get/Update/Delete company |
| GET, POST | `/api/v1/base/departments/` | List/Create departments |
| GET, PUT, DELETE | `/api/v1/base/departments/<id>/` | Get/Update/Delete department |
| GET, POST | `/api/v1/base/worktypes/` | List/Create work types |
| GET, PUT, DELETE | `/api/v1/base/worktypes/<id>/` | Get/Update/Delete work type |
| GET, POST | `/api/v1/base/rotating-worktypes/` | List/Create rotating work types |
| GET, PUT, DELETE | `/api/v1/base/rotating-worktypes/<id>/` | Get/Update/Delete rotating work type |
| GET, POST | `/api/v1/base/rotating-worktype-assigns/` | List/Create rotating work type assigns |
| GET, PUT, DELETE | `/api/v1/base/rotating-worktype-assigns/<id>/` | Get/Update/Delete assign |
| GET, POST | `/api/v1/base/individual-rotating-worktypes/` | List/Create individual rotating work types |
| GET, PUT, DELETE | `/api/v1/base/individual-rotating-worktypes/<id>` | Get/Update/Delete individual work type |
| GET, POST | `/api/v1/base/individual-worktype-request/` | List/Create work type requests |
| GET, PUT, DELETE | `/api/v1/base/individual-worktype-request/<id>` | Get/Update/Delete request |
| GET, POST | `/api/v1/base/employee-shift/` | List/Create employee shifts |
| GET, PUT, DELETE | `/api/v1/base/employee-shift/<id>/` | Get/Update/Delete shift |
| GET, POST | `/api/v1/base/employee-shift-schedules/` | List/Create shift schedules |
| GET, PUT, DELETE | `/api/v1/base/employee-shift-schedules/<id>/` | Get/Update/Delete schedule |
| GET, POST | `/api/v1/base/rotating-shifts/` | List/Create rotating shifts |
| GET, PUT, DELETE | `/api/v1/base/rotating-shifts/<id>/` | Get/Update/Delete rotating shift |
| GET, POST | `/api/v1/base/rotating-shift-assigns/` | List/Create rotating shift assigns |
| GET, PUT, DELETE | `/api/v1/base/rotating-shift-assigns/<id>/` | Get/Update/Delete assign |
| GET, POST | `/api/v1/base/individual-rotating-shifts/` | List/Create individual rotating shifts |
| GET, PUT, DELETE | `/api/v1/base/individual-rotating-shifts/<id>` | Get/Update/Delete individual shift |
| GET, POST | `/api/v1/base/worktype-requests/` | List/Create work type requests |
| GET, PUT, DELETE | `/api/v1/base/worktype-requests/<id>/` | Get/Update/Delete request |
| POST | `/api/v1/base/worktype-requests-cancel/<id>/` | Cancel work type request |
| POST | `/api/v1/base/worktype-requests-approve/<id>/` | Approve work type request |
| GET, POST | `/api/v1/base/shift-requests/` | List/Create shift requests |
| GET, PUT, DELETE | `/api/v1/base/shift-requests/<id>/` | Get/Update/Delete shift request |
| GET, POST | `/api/v1/base/individual-shift-request/` | List/Create individual shift requests |
| GET, PUT, DELETE | `/api/v1/base/individual-shift-request/<id>` | Get/Update/Delete individual request |
| POST | `/api/v1/base/shift-request-approve/<id>` | Approve shift request |
| POST | `/api/v1/base/shift-request-bulk-approve` | Bulk approve shift requests |
| POST | `/api/v1/base/shift-request-cancel/<id>` | Cancel shift request |
| POST | `/api/v1/base/shift-request-bulk-cancel` | Bulk cancel shift requests |
| DELETE | `/api/v1/base/shift-request-delete/<id>` | Delete shift request |
| POST | `/api/v1/base/shift-request-bulk-delete` | Bulk delete shift requests |
| GET | `/api/v1/base/shift-request-export` | Export shift requests |
| GET | `/api/v1/base/shift-request-allocation/<id>` | Get shift request allocation |
| GET | `/api/v1/base/work-type-request-export` | Export work type requests |
| GET | `/api/v1/base/rotating-shift-assign-export` | Export rotating shift assigns |
| POST | `/api/v1/base/rotating-shift-assign-bulk-archive/<status>` | Bulk archive rotating shift assigns |
| POST | `/api/v1/base/rotating-shift-assign-bulk-delete` | Bulk delete rotating shift assigns |
| GET | `/api/v1/base/rotating-worktype-create-permission-check/<id>` | Check rotating work type permission |
| GET | `/api/v1/base/rotating-shift-create-permission-check/<id>` | Check rotating shift permission |
| GET | `/api/v1/base/shift-request-approve-permission-check` | Check shift request approve permission |
| GET | `/api/v1/base/worktype-request-approve-permission-check` | Check work type request approve permission |
| GET | `/api/v1/base/employee-tab-permission-check` | Check employee tab permission |
| GET | `/api/v1/base/check-user-level` | Check user level |

---

## 8. Notifications APIs (`/api/v1/notifications/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications/notifications/list/<type>` | List notifications by type |
| GET, DELETE | `/api/v1/notifications/notifications/<id>/` | Get/Delete notification |
| POST | `/api/v1/notifications/notifications/bulk-delete-unread/` | Bulk delete unread notifications |
| POST | `/api/v1/notifications/notifications/bulk-read/` | Bulk mark as read |
| POST | `/api/v1/notifications/notifications/bulk-delete/` | Bulk delete notifications |

---

## 9. Face Detection APIs (`/api/v1/facedetection/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/facedetection/config/` | Get/Update face detection config |
| GET, POST | `/api/v1/facedetection/employees/` | List/Create employee face records |
| GET, PUT, DELETE | `/api/v1/facedetection/employees/<id>/` | Get/Update/Delete face record |
| POST | `/api/v1/facedetection/verify/` | Verify face for attendance |
| POST | `/api/v1/facedetection/checkin/` | Quick face check-in |
| POST | `/api/v1/facedetection/checkout/` | Quick face check-out |
| POST | `/api/v1/facedetection/validate-image/` | Validate face image |
| GET | `/api/v1/facedetection/status/` | Get face detection status |
| POST | `/api/v1/facedetection/bulk-register/` | Bulk register faces |
| GET | `/api/v1/facedetection/stats/` | Get face recognition statistics |

---

## 10. Recruitment APIs (`/api/v1/recruitment/`) - NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/recruitment/recruitments/` | List/Create recruitments |
| GET, PUT, DELETE | `/api/v1/recruitment/recruitments/<id>/` | Get/Update/Delete recruitment |
| GET, POST | `/api/v1/recruitment/candidates/` | List/Create candidates |
| GET, PUT, DELETE | `/api/v1/recruitment/candidates/<id>/` | Get/Update/Delete candidate |
| GET, POST | `/api/v1/recruitment/stages/` | List/Create stages |
| GET, PUT, DELETE | `/api/v1/recruitment/stages/<id>/` | Get/Update/Delete stage |
| GET, POST | `/api/v1/recruitment/interviews/` | List/Create interview schedules |
| GET, PUT, DELETE | `/api/v1/recruitment/interviews/<id>/` | Get/Update/Delete interview |
| GET, POST | `/api/v1/recruitment/survey-templates/` | List/Create survey templates |
| GET, PUT, DELETE | `/api/v1/recruitment/survey-templates/<id>/` | Get/Update/Delete survey template |
| GET, POST | `/api/v1/recruitment/skills/` | List/Create skills |
| GET, PUT, DELETE | `/api/v1/recruitment/skills/<id>/` | Get/Update/Delete skill |

---

## 11. PMS (Performance Management) APIs (`/api/v1/pms/`) - NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/pms/periods/` | List/Create periods |
| GET, PUT, DELETE | `/api/v1/pms/periods/<id>/` | Get/Update/Delete period |
| GET, POST | `/api/v1/pms/key-results/` | List/Create key results |
| GET, PUT, DELETE | `/api/v1/pms/key-results/<id>/` | Get/Update/Delete key result |
| GET, POST | `/api/v1/pms/objectives/` | List/Create objectives |
| GET, PUT, DELETE | `/api/v1/pms/objectives/<id>/` | Get/Update/Delete objective |
| GET, POST | `/api/v1/pms/employee-objectives/` | List/Create employee objectives |
| GET, PUT, DELETE | `/api/v1/pms/employee-objectives/<id>/` | Get/Update/Delete employee objective |
| GET, POST | `/api/v1/pms/employee-key-results/` | List/Create employee key results |
| GET, PUT, DELETE | `/api/v1/pms/employee-key-results/<id>/` | Get/Update/Delete employee key result |
| GET, POST | `/api/v1/pms/feedback/` | List/Create feedback |
| GET, PUT, DELETE | `/api/v1/pms/feedback/<id>/` | Get/Update/Delete feedback |
| GET, POST | `/api/v1/pms/question-templates/` | List/Create question templates |
| GET, PUT, DELETE | `/api/v1/pms/question-templates/<id>/` | Get/Update/Delete question template |
| GET, POST | `/api/v1/pms/questions/` | List/Create questions |
| GET, PUT, DELETE | `/api/v1/pms/questions/<id>/` | Get/Update/Delete question |
| GET, POST | `/api/v1/pms/question-options/` | List/Create question options |
| GET, PUT, DELETE | `/api/v1/pms/question-options/<id>/` | Get/Update/Delete question option |
| GET, POST | `/api/v1/pms/answers/` | List/Create answers |
| GET, PUT, DELETE | `/api/v1/pms/answers/<id>/` | Get/Update/Delete answer |
| GET, POST | `/api/v1/pms/meetings/` | List/Create meetings |
| GET, PUT, DELETE | `/api/v1/pms/meetings/<id>/` | Get/Update/Delete meeting |
| GET, POST | `/api/v1/pms/meetings-answers/` | List/Create meeting answers |
| GET, PUT, DELETE | `/api/v1/pms/meetings-answers/<id>/` | Get/Update/Delete meeting answer |
| GET, POST | `/api/v1/pms/employee-bonus-points/` | List/Create employee bonus points |
| GET, PUT, DELETE | `/api/v1/pms/employee-bonus-points/<id>/` | Get/Update/Delete employee bonus point |
| GET, POST | `/api/v1/pms/bonus-point-settings/` | List/Create bonus point settings |
| GET, PUT, DELETE | `/api/v1/pms/bonus-point-settings/<id>/` | Get/Update/Delete bonus point setting |

---

## 12. Onboarding APIs (`/api/v1/onboarding/`) - NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/onboarding/stages/` | List/Create onboarding stages |
| GET, PUT, DELETE | `/api/v1/onboarding/stages/<id>/` | Get/Update/Delete onboarding stage |
| GET, POST | `/api/v1/onboarding/tasks/` | List/Create onboarding tasks |
| GET, PUT, DELETE | `/api/v1/onboarding/tasks/<id>/` | Get/Update/Delete onboarding task |
| GET, POST | `/api/v1/onboarding/candidate-stages/` | List/Create candidate stages |
| GET, PUT, DELETE | `/api/v1/onboarding/candidate-stages/<id>/` | Get/Update/Delete candidate stage |
| GET, POST | `/api/v1/onboarding/candidate-tasks/` | List/Create candidate tasks |
| GET, PUT, DELETE | `/api/v1/onboarding/candidate-tasks/<id>/` | Get/Update/Delete candidate task |
| GET, POST | `/api/v1/onboarding/portals/` | List/Create onboarding portals |
| GET, PUT, DELETE | `/api/v1/onboarding/portals/<id>/` | Get/Update/Delete onboarding portal |

---

## 13. Offboarding APIs (`/api/v1/offboarding/`) - NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/offboarding/offboardings/` | List/Create offboardings |
| GET, PUT, DELETE | `/api/v1/offboarding/offboardings/<id>/` | Get/Update/Delete offboarding |
| GET, POST | `/api/v1/offboarding/stages/` | List/Create offboarding stages |
| GET, PUT, DELETE | `/api/v1/offboarding/stages/<id>/` | Get/Update/Delete offboarding stage |
| GET, POST | `/api/v1/offboarding/employees/` | List/Create offboarding employees |
| GET, PUT, DELETE | `/api/v1/offboarding/employees/<id>/` | Get/Update/Delete offboarding employee |
| GET, POST | `/api/v1/offboarding/resignation-letters/` | List/Create resignation letters |
| GET, PUT, DELETE | `/api/v1/offboarding/resignation-letters/<id>/` | Get/Update/Delete resignation letter |
| GET, POST | `/api/v1/offboarding/tasks/` | List/Create offboarding tasks |
| GET, PUT, DELETE | `/api/v1/offboarding/tasks/<id>/` | Get/Update/Delete offboarding task |
| GET, POST | `/api/v1/offboarding/employee-tasks/` | List/Create employee tasks |
| GET, PUT, DELETE | `/api/v1/offboarding/employee-tasks/<id>/` | Get/Update/Delete employee task |
| GET, POST | `/api/v1/offboarding/exit-reasons/` | List/Create exit reasons |
| GET, PUT, DELETE | `/api/v1/offboarding/exit-reasons/<id>/` | Get/Update/Delete exit reason |
| GET, POST | `/api/v1/offboarding/notes/` | List/Create offboarding notes |
| GET, PUT, DELETE | `/api/v1/offboarding/notes/<id>/` | Get/Update/Delete offboarding note |
| GET, POST | `/api/v1/offboarding/settings/` | List/Create offboarding settings |
| GET, PUT, DELETE | `/api/v1/offboarding/settings/<id>/` | Get/Update/Delete offboarding setting |

---

## 14. Helpdesk APIs (`/api/v1/helpdesk/`) - NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/helpdesk/tickets/` | List/Create tickets |
| GET, PUT, DELETE | `/api/v1/helpdesk/tickets/<id>/` | Get/Update/Delete ticket |
| GET, POST | `/api/v1/helpdesk/ticket-types/` | List/Create ticket types |
| GET, PUT, DELETE | `/api/v1/helpdesk/ticket-types/<id>/` | Get/Update/Delete ticket type |
| GET, POST | `/api/v1/helpdesk/comments/` | List/Create comments |
| GET, PUT, DELETE | `/api/v1/helpdesk/comments/<id>/` | Get/Update/Delete comment |
| GET, POST | `/api/v1/helpdesk/attachments/` | List/Create attachments |
| GET, PUT, DELETE | `/api/v1/helpdesk/attachments/<id>/` | Get/Update/Delete attachment |
| GET, POST | `/api/v1/helpdesk/faqs/` | List/Create FAQs |
| GET, PUT, DELETE | `/api/v1/helpdesk/faqs/<id>/` | Get/Update/Delete FAQ |
| GET, POST | `/api/v1/helpdesk/faq-categories/` | List/Create FAQ categories |
| GET, PUT, DELETE | `/api/v1/helpdesk/faq-categories/<id>/` | Get/Update/Delete FAQ category |
| GET, POST | `/api/v1/helpdesk/department-managers/` | List/Create department managers |
| GET, PUT, DELETE | `/api/v1/helpdesk/department-managers/<id>/` | Get/Update/Delete department manager |
| GET, POST | `/api/v1/helpdesk/claim-requests/` | List/Create claim requests |
| GET, PUT, DELETE | `/api/v1/helpdesk/claim-requests/<id>/` | Get/Update/Delete claim request |

---

## 15. Project APIs (`/api/v1/project/`) - NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/project/projects/` | List/Create projects |
| GET, PUT, DELETE | `/api/v1/project/projects/<id>/` | Get/Update/Delete project |
| GET, POST | `/api/v1/project/stages/` | List/Create project stages |
| GET, PUT, DELETE | `/api/v1/project/stages/<id>/` | Get/Update/Delete project stage |
| GET, POST | `/api/v1/project/tasks/` | List/Create tasks |
| GET, PUT, DELETE | `/api/v1/project/tasks/<id>/` | Get/Update/Delete task |
| GET, POST | `/api/v1/project/timesheets/` | List/Create timesheets |
| GET, PUT, DELETE | `/api/v1/project/timesheets/<id>/` | Get/Update/Delete timesheet |

---

## 16. Geofencing APIs (`/api/v1/geofencing/`) - NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/v1/geofencing/geofencings/` | List/Create geofencing configurations |
| GET, PUT, DELETE | `/api/v1/geofencing/geofencings/<id>/` | Get/Update/Delete geofencing |

---

## Postman Collection Setup

### Step 1: Create Environment Variables
- `base_url` = `http://127.0.0.1:8000/api/v1`
- `access_token` = (will be set automatically after login)

### Step 2: Setup Authentication
1. Create a request: `POST {{base_url}}/auth/login/`
2. Body (JSON):
```json
{
  "username": "your_username",
  "password": "your_password"
}
```
3. In Tests tab, add:
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access);
}
```

### Step 3: Set Collection-Level Authorization
- Type: Bearer Token
- Token: `{{access_token}}`

### Step 4: Create Folders
Organize requests by module:
- Authentication
- Employee
- Attendance
- Leave
- Payroll
- Asset
- Base
- Notifications
- Face Detection
- Recruitment (NEW)
- PMS (NEW)
- Onboarding (NEW)
- Offboarding (NEW)
- Helpdesk (NEW)
- Project (NEW)
- Geofencing (NEW)

---

## Total API Endpoints

**Total: 200+ API endpoints** across 16 modules

All endpoints support standard CRUD operations (GET, POST, PUT, DELETE) where applicable, with pagination for list endpoints.

