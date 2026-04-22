# Copyright (c) 2026, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from collections import defaultdict
from frappe.utils import cint

def execute(filters=None):
	if not filters : filters = {}
	columns, data = [], []
	
	columns = get_columns()
	data = get_data(filters)
	
	if not data :
		frappe.msgprint('No Records Found')
		return columns, data
	
	return columns, data

def get_columns():
	columns = [
		{
			"fieldname" :"employee",
			"fieldtype" :"Link",
			"label" :"Employee Code",
			"options" : "Employee",
			"width" :150
		},
		{
			"fieldname" :"employee_name",
			"fieldtype" :"Data",
			"label" :"Employee Name",
			"width" :250
		},
		{
			"fieldname" :"clr_id",
			"fieldtype" :"Link",
			"label" :"Compensatory Leave Request Id",
			"options" : "Compensatory Leave Request",
			"width" :240
		},
		{
			"fieldname" :"worked_on_holiday",
			"fieldtype" :"Date",
			"label" :"Worked On Holiday",
			"width" : 160
		},
		{
			"fieldname" :"leave_application_id",
			"fieldtype" :"Link",
			"label" :"Leave Application Id",
			"options" : "Leave Application",
			"width" :180
		},
		{
			"fieldname" :"comp_off_taken_date",
			"fieldtype" :"Date",
			"label" :"Compensatory Off Taken",
			"width" :200
		},
	]
	return columns


def get_data(filters):
	conditions = get_conditions(filters)
	data = []
	unique_employee_list = frappe.db.sql_list("""SELECT DISTINCT clr.employee FROM `tabCompensatory Leave Request` AS clr WHERE docstatus = 1 {0}""".format(conditions))
	# print(unique_employee_list, "========unique_employee_list===")
	if len(unique_employee_list) > 0:
		for emp in unique_employee_list:
			emp_clr_list = frappe.db.sql("""
							SELECT 
								clr.employee, clr.employee_name, clr.work_from_date AS worked_on_holiday, clr.name AS clr_id  FROM `tabCompensatory Leave Request` AS clr
							WHERE clr.docstatus = 1 AND clr.employee = '{0}' AND clr.work_from_date BETWEEN '{1}' AND '{2}'
							ORDER BY clr.work_from_date  """.format(emp, filters["from_date"], filters["to_date"]), as_dict=1)
			
			emp_leave_application = frappe.db.sql("""
									SELECT 
										la.employee, la.from_date, la.total_leave_days, la.name FROM `tabLeave Application` AS la
									WHERE la.status = "Approved" AND la.docstatus = 1 AND
 										la.leave_type = (SELECT value FROM `tabSingles` WHERE doctype = "Mech Attendance Settings" AND field = "default_compensatory_off_leave_type")
											AND la.employee = '{0}' AND la.from_date BETWEEN '{1}' AND '{2}'
									ORDER BY la.from_date """.format(emp, filters["from_date"], filters["to_date"]), as_dict=1, debug=1)		

			emp_leave_per_date_details = []
			i = 0   ## for comparing row id with clr row
			if len(emp_leave_application) > 0:
				for leave in emp_leave_application:
					leave_dates = get_date_list(leave.from_date, cint(leave.total_leave_days))
					for date in leave_dates:
						i += 1
						emp_leave_per_date_details.append({
							"employee": leave.employee,
							"comp_off_taken_date": date,
							"leave_application_id": leave.name,
							"id": i
						})

			compensatory_off_data = []
			for idx, clr in enumerate(emp_clr_list, start=1):
				merged_row = clr.copy()  ## to avoid updating clr dict in each iteration
				merged_row["id"] = idx
				for la in emp_leave_per_date_details:
					if la["id"] == idx:
						merged_row.update(la)
						break

				if idx != 1:   ## only add employee in first row 
					merged_row["employee"] = None
					merged_row["employee_name"] = None
				compensatory_off_data.append(merged_row)

			data.extend(compensatory_off_data)

	return data

def get_conditions(filters):
	conditions = ""
	
	if filters.get("employee"):
		conditions += " AND employee = '{0}'".format(filters["employee"])
		
	if filters.get("from_date") and filters.get("to_date"):
		conditions += "AND clr.work_from_date BETWEEN '{0}' AND '{1}'".format(filters["from_date"],filters["to_date"])
   
	return conditions

def get_date_list(from_date, total_days):
	date_list = []
	for day in range(total_days):
		date = frappe.utils.add_days(from_date, day)
		date_list.append(date)
	return date_list