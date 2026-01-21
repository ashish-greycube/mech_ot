import frappe

def get_fixed_component_values(employee, salary_slip):
    fixed = {}
    if employee and salary_slip:
        salary_structure_assignment = frappe.db.get_all("Salary Structure Assignment", {"employee": employee, "docstatus": 1}, pluck="name", order_by="creation DESC")
        if salary_structure_assignment:
            doc = frappe.get_doc("Salary Structure Assignment", salary_structure_assignment)
            fixed.update({
                "Basic": doc.base,
                "House Rent Allowance": doc.custom_hra,
                "Medical Allowance": doc.custom_medical_allowance,
                "Conveyance": doc.custom_conveyance,
                "City Allowance": doc.custom_city_allowance,
                "R & D Allowance": doc.custom_r_d_allowance,
                "On Site Allowance": doc.custom_on_site_allowance,
                "Misc Allowance": doc.custom_misc_allowance,
                "Project Allowance": doc.custom_project_allowance,
                "Variable Pay": doc.custom_vpf,
            })
    return fixed

def get_leave_balance_of_employee(employee, start_date):
    balances = {}
    from hrms.hr.report.employee_leave_balance.employee_leave_balance import execute
    from erpnext.accounts.utils import get_fiscal_year
    data = execute(frappe._dict({
        "from_date":get_fiscal_year(start_date)[1],
        "to_date": get_fiscal_year(start_date)[2],
        "employee": employee
    }))
    
    if len(data) > 0:
        for d in data[1]:
            balances[d.leave_type] = {
                "opening_balance": d.opening_balance + d.leaves_allocated,
                "leaves_taken": d.leaves_taken,
                "closing_balance": d.closing_balance
            }
    return balances

def get_overtime_hours(employee, start_date, end_date):
    overtime_hours = frappe.db.sql("""
        SELECT 
            at.employee, 
            sum(at.custom_rounded_extra_working_hours) as total_ot_hours
        FROM `tabAttendance` as at
            INNER JOIN `tabEmployee` as e ON at.employee = e.name
        WHERE at.docstatus = 1
        AND at.attendance_date BETWEEN '{0}' AND '{1}'
        AND at.custom_rounded_extra_working_hours > 0 
        AND at.employee = '{2}'
        GROUP BY at.employee
        ORDER BY at.employee
    """.format(start_date, end_date, employee), debug=1, as_dict=1)
    return overtime_hours