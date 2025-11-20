# Copyright (c) 2025, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OvertimeWorkingSheet(Document):

	def on_submit(self):
		ot_salary_component = frappe.db.get_single_value("Mech OT Settings", "overtime_earning_component")
		if not ot_salary_component:
			frappe.throw("Please set Overtime Earning Component in Mech OT Settings")
		for row in self.overtime_working_sheet_employee_details:
			additional_salary_doc = frappe.get_doc({
				"doctype": "Additional Salary",
				"employee": row.employee,
				"salary_component": ot_salary_component,
				"amount": row.ot_amount,
				"payroll_date": self.posting_date,
				"overtime_working_sheet": self.name,
				"ref_doctype": "Overtime Working Sheet",
				"ref_docname": self.name
			})
			additional_salary_doc.insert()
			additional_salary_doc.submit()
	
	@frappe.whitelist()
	def fetch_employee(self):
		employee_filters = ""
		if self.branch:
			employee_filters += " AND e.branch = '{0}' ".format(self.branch)
		if self.department:
			employee_filters += " AND e.department = '{0}' ".format(self.department)
		if self.designation:
			employee_filters += " AND e.designation = '{0}' ".format(self.designation)
		if self.grade:
			employee_filters += " AND e.grade = '{0}' ".format(self.grade)
		
		attendance_records = frappe.db.sql("""
			SELECT 
					at.employee, 
					at.employee_name, 
					sum(at.custom_rounded_extra_working_hours) as total_ot_hours, 
					sum(at.custom_overtime_amount) as total_ot_amount,
					at.custom_overtime_rate,
					e.department,
					e.designation
			FROM `tabAttendance` as at
				INNER JOIN `tabEmployee` as e ON at.employee = e.name
			WHERE at.docstatus = 1
			AND at.attendance_date BETWEEN '{0}' AND '{1}'
			AND at.custom_rounded_extra_working_hours > 0 {2}
			GROUP BY at.employee
			ORDER BY at.employee
		""".format(self.start_date, self.end_date, employee_filters),debug=1, as_dict=1)

		if len(attendance_records) == 0:
			frappe.throw("No Overtime Attendance records found for the selected criteria")
		elif len(attendance_records) > 0:
			self.overtime_working_sheet_employee_details = []
			for attendance in attendance_records:
				child = self.append("overtime_working_sheet_employee_details", {})
				child.employee = attendance.employee
				child.employee_name = attendance.employee_name
				child.ot_total_hours = attendance.total_ot_hours
				child.ot_rate = attendance.custom_overtime_rate
				child.ot_amount = attendance.total_ot_amount
				child.department = attendance.department
				child.designation = attendance.designation
			# self.save()