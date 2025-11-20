# Copyright (c) 2025, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []

	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns():
	columns = [
		{"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options":"Employee", "width": 300},
		# {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 150},
		{"label": "Overtime Hours", "fieldname": "overtime_hours", "fieldtype": "Float", "width": 150},
		{"label": "Overtime Rate", "fieldname": "overtime_rate", "fieldtype": "Currency", "width": 150},
		{"label": "Overtime Amount", "fieldname": "overtime_amount", "fieldtype": "Currency", "width": 150},
	]
	return columns

def get_data(filters):
	conditions = ""
	if filters.get("employee"):
		conditions += " AND employee = '{0}' ".format(filters.get("employee"))
	if filters.get("from_date"):
		conditions += " AND attendance_date >= '{0}' ".format(filters.get("from_date"))
	if filters.get("to_date"):
		conditions += " AND attendance_date <= '{0}' ".format(filters.get("to_date"))

	data = frappe.db.sql("""
		SELECT 
			employee,
			employee_name,
			attendance_date as date,
			custom_rounded_extra_working_hours as overtime_hours,
			custom_overtime_rate as overtime_rate,
			custom_overtime_amount as overtime_amount
		FROM `tabAttendance`
		WHERE docstatus = 1
		AND custom_rounded_extra_working_hours > 0
		{0}
		ORDER BY employee, attendance_date
	""".format(conditions), as_dict=1)

	return data