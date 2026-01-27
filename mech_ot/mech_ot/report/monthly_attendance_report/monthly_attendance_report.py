# Copyright (c) 2026, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
import erpnext
from frappe import _
import datetime
from frappe.utils import cint, cstr, getdate
from frappe.utils.nestedset import get_descendants_of
from frappe.query_builder.functions import Extract

def execute(filters=None):
	if not filters: 
		filters = {}
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	message = "Time Format For In-Time, Out-Time, Last CheckIn & Early Exit Is <b><i>HH:MM:SS</i></b>"
	return columns, data, message

def get_columns(filters):
	columns = [
		{
			'fieldname' : 'employee',
			'fieldtype' : 'Link',
			'label' : _('Employee'),
			'options' : 'Employee',
			'width' : 300,
		},
		{
			'fieldname' : 'employee_name',
			'fieldtype' : 'Data',
			'label' : _('Employee Name'),
			'width' : 180,
		},
		{
			'fieldname' : 'detail',
			'fieldtype' : 'Data',
			'label' : _('Detail Type'),
			'width' : 130,
		},
	]

	total_days = frappe.utils.date_diff(frappe.utils.getdate(filters.get('to_date')), frappe.utils.getdate(filters.get('from_date')))

	i = 1
	for day in range(0, total_days+1):
		dayname = frappe.utils.getdate(frappe.utils.add_to_date(filters.get('from_date'), days=day)).strftime("%a")
		day = frappe.utils.cint(frappe.utils.getdate(frappe.utils.add_to_date(filters.get('from_date'), days=day)).strftime("%d"))
		
		col = {
			'fieldname' : i,
			'fieldtype' : 'Data',
			'label' : "{0} {1}".format(day, dayname),
			'width' : 100,
		}
		columns.append(col)
		i = i + 1
	
	columns.extend([
		{
			'fieldname' : 'total',
			'fieldtype' : 'Data',
			'label' : _('Total'),
			'width' : 130,
		},
		{
			'fieldname' : 'total_days_present',
			'fieldtype' : 'Data',
			'label' : _('Total Days Present'),
			'width' : 150,
		},
		{
			'fieldname' : 'total_days_absent',
			'fieldtype' : 'Data',
			'label' : _('Total Days Absent'),
			'width' : 150,
		},
		{
			'fieldname' : 'total_ot_hours',
			'fieldtype' : 'Data',
			'label' : _('Total OT Hours'),
			'width' : 150,
		},
	])

	leaves = frappe.db.get_all(
		doctype = "Leave Type",
		filters = {},
		pluck = "name",
		order_by = "name DESC"
	)
	casual = leaves.remove("Casual Leave")
	leaves.insert(0, "Casual Leave")
	
	for leave in leaves:
		columns.append({
			'fieldname' : leave.lower().replace(" ", "_"),
			'fieldtype' : 'Data',
			'label' : "{0}".format(leave),
			'width' : 180,
		})

	columns.append({
		'fieldname' : "total_days_on_leave",
		'fieldtype' : 'Data',
		'label' : "Total Days On Leave",
		'width' : 180,
	})

	return columns

def get_filtered_data(filters, report_rows):
	filtered_data = []
	if filters.get("shift") and filters.get('employee') and  filters.get("department") and filters.get("category"):
		for rr in report_rows:
			if (rr['shift'] == filters.get("shift")) and (('employee' in rr and rr['employee'] == filters.get("employee")) or ('hidden_employee' in rr and rr['hidden_employee'] == filters.get("employee"))) and (rr['department'] == filters.get("department")) and rr['category'] == filters.get("category"):
				filtered_data.append(rr)
		return filtered_data

	if filters.get("shift") and filters.get('employee'):
		for rr in report_rows:
			if (rr['shift'] == filters.get("shift")) and ('employee' in rr and rr['employee'] == filters.get("employee")) or ('hidden_employee' in rr and rr['hidden_employee'] == filters.get("employee")):
				filtered_data.append(rr)
		return filtered_data
	
	if filters.get("category") and filters.get('employee'):
		for rr in report_rows:
			if (rr['category'] == filters.get("category")) and ('employee' in rr and rr['employee'] == filters.get("employee")) or ('hidden_employee' in rr and rr['hidden_employee'] == filters.get("employee")):
				filtered_data.append(rr)
		return filtered_data
	
	if filters.get("shift") and filters.get('department'):
		for rr in report_rows:
			if (rr['shift'] == filters.get("shift")) and (rr['department'] == filters.get("department")):
				filtered_data.append(rr)
		return filtered_data
	
	if filters.get("shift") and filters.get('category'):
		for rr in report_rows:
			if (rr['shift'] == filters.get("shift")) and (rr['category'] == filters.get("category")):
				filtered_data.append(rr)
		return filtered_data
	
	if filters.get("employee") and filters.get('department'):
		for rr in report_rows:
			if ('employee' in rr and rr['employee'] == filters.get("employee")) or ('hidden_employee' in rr and rr['hidden_employee'] == filters.get("employee")) and (rr['department'] == filters.get("department")):
				filtered_data.append(rr)
		return filtered_data

	if filters.get("shift"):
		for rr in report_rows:
			if rr['shift'] == filters.get("shift"):
				filtered_data.append(rr)
		return filtered_data

	if filters.get('employee'):
		for rr in report_rows:
			if ('employee' in rr and rr['employee'] == filters.get("employee")) or ('hidden_employee' in rr and rr['hidden_employee'] == filters.get("employee")):
				filtered_data.append(rr)
		return filtered_data
	
	if filters.get("department"):
		for rr in report_rows:
			if rr['department'] == filters.get("department"):
				filtered_data.append(rr)
		return filtered_data
	
	if filters.get("category"):
		for rr in report_rows:
			if rr['category'] == filters.get("category"):
				filtered_data.append(rr)
		return filtered_data


def get_monthly_attendance_sheet_report_data(filters):
	ref_filters = frappe._dict({
		'from_date' : filters.get('from_date'),
		'to_date' : filters.get('to_date'),
		'month' : frappe.utils.getdate(filters.get('from_date')).strftime("%b"),
		'year' : frappe.utils.getdate(filters.get('from_date')).strftime("%Y"),
		'company' : erpnext.get_default_company(),
		'include_company_descendants' : 1,
	})

	Filters = ref_filters

	status_map = {
		"Present": "P",
		"Absent": "A",
		"Half Day": "HD",
		"Work From Home": "WFH",
		"On Leave": "L",
		"Holiday": "H",
		"Weekly Off": "WO",
	}

	day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


	def _execute(filters: Filters) -> tuple:
		filters = frappe._dict(filters or {})
	
		if not (filters.month and filters.year):
			frappe.throw(_("Please select month and year."))

		if not filters.company:
			frappe.throw(_("Please select company."))

		if filters.company:
			filters.companies = [filters.company]
			if filters.include_company_descendants:
				filters.companies.extend(get_descendants_of("Company", filters.company))

		attendance_map = get_attendance_map(filters)
		if not attendance_map:
			# frappe.msgprint(_("No attendance records found."), alert=True, indicator="orange")
			return [], [], None, None

		columns = get_columns(filters)
		data = get_data(filters, attendance_map)

		return columns, data


	def get_columns(filters: Filters) -> list[dict]:
		columns = []
		columns.extend(
			[
				{
					"label": _("Employee"),
					"fieldname": "employee",
					"fieldtype": "Link",
					"options": "Employee",
					"width": 135,
				},
				{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 120},
			]
		)
		columns.append({"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 120})
		
		return columns

	def get_total_days_in_month(filters: Filters) -> int:
		return frappe.utils.date_diff(frappe.utils.getdate(filters.get('to_date')), frappe.utils.getdate(filters.get('from_date')))

	def get_data(filters: Filters, attendance_map: dict) -> list[dict]:
		employee_details, group_by_param_values = get_employee_related_details(filters)
		holiday_map = get_holiday_map(filters)
		data = []

		data = get_rows(employee_details, filters, holiday_map, attendance_map)

		return data


	def get_attendance_map(filters: Filters) -> dict:
		"""Returns a dictionary of employee wise attendance map as per shifts for all the days of the month like
		{
			'employee1': {
					'Morning Shift': {1: 'Present', 2: 'Absent', ...}
					'Evening Shift': {1: 'Absent', 2: 'Present', ...}
			},
			'employee2': {
					'Afternoon Shift': {1: 'Present', 2: 'Absent', ...}
					'Night Shift': {1: 'Absent', 2: 'Absent', ...}
			},
			'employee3': {
					None: {1: 'On Leave'}
			}
		}
		"""
		
		attendance_list = get_attendance_records(filters)
		
		attendance_map = {}
		leave_map = {}

		for d in attendance_list:
			if d.status == "On Leave":
				leave_map.setdefault(d.employee, {}).setdefault(d.shift, []).append(d.day_of_month)
				continue

			if d.shift is None:
				d.shift = ""

			attendance_map.setdefault(d.employee, {}).setdefault(d.shift, {})
			attendance_map[d.employee][d.shift][d.day_of_month] = d.status

		# leave is applicable for the entire day so all shifts should show the leave entry
		for employee, leave_days in leave_map.items():
			for assigned_shift, days in leave_days.items():
				# no attendance records exist except leaves
				if employee not in attendance_map:
					attendance_map.setdefault(employee, {}).setdefault(assigned_shift, {})

				for day in days:
					for shift in attendance_map[employee].keys():
						attendance_map[employee][shift][day] = "On Leave"
	
		return attendance_map

	def get_attendance_records(filters: Filters) -> list[dict]:
		Attendance = frappe.qb.DocType("Attendance")
		query = (
			frappe.qb.from_(Attendance)
			.select(
				Attendance.employee,
				Extract("day", Attendance.attendance_date).as_("day_of_month"),
				Attendance.status,
				Attendance.shift,
				Attendance.in_time,
				Attendance.out_time,
				Attendance.late_entry,
				Attendance.early_exit,
				Attendance.working_hours,
				Attendance.custom_rounded_extra_working_hours,
			)
			.where(
				(Attendance.docstatus == 1)
				& (Attendance.company.isin(filters.companies))
				& (Attendance.attendance_date >= frappe.utils.getdate(filters.get('from_date')))
				& (Attendance.attendance_date <= frappe.utils.getdate(filters.get('to_date')))
			)
		)

		if filters.employee:
			query = query.where(Attendance.employee == filters.employee)
		query = query.orderby(Attendance.employee, Attendance.attendance_date)

		return query.run(as_dict=1)

	def get_employee_related_details(filters: Filters) -> tuple[dict, list]:
		"""Returns
		1. nested dict for employee details
		2. list of values for the group by filter
		"""
		Employee = frappe.qb.DocType("Employee")
		query = (
			frappe.qb.from_(Employee)
			.select(
				Employee.name,
				Employee.employee_name,
				Employee.designation,
				Employee.grade,
				Employee.department,
				Employee.branch,
				Employee.company,
				Employee.holiday_list,
			)
			.where(
				(Employee.company.isin(filters.companies))
				& (Employee.status == "Active")
			)
		)

		if filters.employee:
			query = query.where(Employee.name == filters.employee)

		employee_details = query.run(as_dict=True)

		group_by_param_values = []
		emp_map = {}

		for emp in employee_details:
			emp_map[emp.name] = emp

		return emp_map, group_by_param_values


	def get_holiday_map(filters: Filters) -> dict[str, list[dict]]:
		"""
		Returns a dict of holidays falling in the filter month and year
		with list name as key and list of holidays as values like
		{
				'Holiday List 1': [
						{'day_of_month': '0' , 'weekly_off': 1},
						{'day_of_month': '1', 'weekly_off': 0}
				],
				'Holiday List 2': [
						{'day_of_month': '0' , 'weekly_off': 1},
						{'day_of_month': '1', 'weekly_off': 0}
				]
		}
		"""
		# add default holiday list too
		holiday_lists = frappe.db.get_all("Holiday List", pluck="name")
		default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")
		holiday_lists.append(default_holiday_list)

		holiday_map = frappe._dict()
		Holiday = frappe.qb.DocType("Holiday")

		for d in holiday_lists:
			if not d:
				continue

			holidays = (
				frappe.qb.from_(Holiday)
				.select(Extract("day", Holiday.holiday_date).as_("day_of_month"), Holiday.weekly_off)
				.where(
					(Holiday.parent == d)
					& (Holiday.holiday_date >= frappe.utils.getdate(filters.get("from_date")))
					& (Holiday.holiday_date <= frappe.utils.getdate(filters.get("to_date")))
				)
			).run(as_dict=True)

			holiday_map.setdefault(d, holidays)

		return holiday_map


	def get_rows(employee_details: dict, filters: Filters, holiday_map: dict, attendance_map: dict) -> list[dict]:
		records = []
		default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")

		for employee, details in employee_details.items():
			emp_holiday_list = details.holiday_list or default_holiday_list
			holidays = holiday_map.get(emp_holiday_list)

			employee_attendance = attendance_map.get(employee)
			if not employee_attendance:
				continue
			attendance_for_employee = get_attendance_status_for_detailed_view(
				employee, filters, employee_attendance, holidays
			)
			# set employee details in the first row
			attendance_for_employee[0].update({"employee": employee, "employee_name": details.employee_name})

			records.extend(attendance_for_employee)
		return records

	def get_attendance_status_for_detailed_view(
		employee: str, filters: Filters, employee_attendance: dict, holidays: list
	) -> list[dict]:
		"""Returns list of shift-wise attendance status for employee
		[
				{'shift': 'Morning Shift', 1: 'A', 2: 'P', 3: 'A'....},
				{'shift': 'Evening Shift', 1: 'P', 2: 'A', 3: 'P'....}
		]
		"""
		total_days = get_total_days_in_month(filters)
		attendance_values = []
		
		for shift, status_dict in employee_attendance.items():
			row = {"shift": shift}
			
			for day in range(0, total_days+1):
				day = cint(frappe.utils.getdate(frappe.utils.add_to_date(filters.get('from_date'), days=day)).strftime("%d"))
				status = status_dict.get(day)
				if status is None and holidays:
					status = get_holiday_status(day, holidays)

				abbr = status_map.get(status, "")
				row[cstr(day)] = abbr

			attendance_values.append(row)

		return attendance_values


	def get_holiday_status(day: int, holidays: list) -> str:
		status = None
		if holidays:
			for holiday in holidays:
				if day == holiday.get("day_of_month"):
					if holiday.get("weekly_off"):
						status = "Weekly Off"
					else:
						status = "Holiday"
					break
		return status
	
	result = _execute(Filters)
	return result

def get_leaves_counts_of_employees(filters):
	employee_leaves_dict = {}
	employees = frappe.db.get_all("Employee", {"status": "active"}, pluck = "name")
	if employees:
		for employee in employees:
			leaves = frappe.db.sql(
				'''
				SELECT leave_type, count(name) as "count"
				FROM `tabLeave Application`
				WHERE from_date BETWEEN "{1}" AND "{0}"
				AND to_date BETWEEN "{1}" AND "{0}"
				AND employee = "{2}"
				GROUP BY leave_type
				'''.format(filters.get("to_date"), filters.get("from_date"), employee), as_dict = 1
			)
			employee_leaves_dict[employee] = leaves
	return employee_leaves_dict

def get_data(filters):
	attendance_month = frappe.utils.getdate(filters.get("from_date")).strftime("%m")
	attendance_year = frappe.utils.getdate(filters.get("from_date")).strftime("%Y")
	employee_leaves_map = get_leaves_counts_of_employees(filters)

	leaves = frappe.db.get_all( "Leave Type", {}, pluck="name" )

	# Reference Report Data
	data = get_monthly_attendance_sheet_report_data(filters)
	data = data[1]
	
	# Creating Employee Attendance Map For Optimazation
	employee_times_map = {} 
	end_date = filters.get('to_date') ,
	start_date =  filters.get('from_date')

	employee_times = frappe.db.sql("""
		select employee , in_time , out_time , late_entry , early_exit , working_hours , attendance_date, shift, department, employee_name, custom_rounded_extra_working_hours
		from tabAttendance ta 
		where attendance_date between %s and %s
		order by employee
	""",(start_date , end_date), as_dict = True)

	for d in employee_times:
		employee_times_map[d['employee']+ "-" +str(int(frappe.utils.getdate(d['attendance_date']).strftime('%d')))] = d

	# For Each Employee Finding Daywise Map + Assigning Status 
	for d in data:
		for col in d:
			if col in ['shift', 'employee', 'employee_name']:
				continue

			if not 'employee' in d:
				continue

			status = d[col]
			no_attendance_dict = {
				"employee": d['employee'],
				"in_time":"-",
				"out_time":"-",
				"late_entry":0,
				"early_exit":0,
				"working_hours":0.0,
				"shift" : None,
				"department" : None
			}
			alternate_status = ""
			
			if getdate(f"{attendance_year}-{attendance_month}-{col}") < getdate():
				alternate_status = "A"
			else:
				alternate_status = ""
			d[col] = employee_times_map[d['employee']+ "-" +col] if d['employee']+ "-" +col in employee_times_map else no_attendance_dict
			d[col]['status'] = status or alternate_status

	# Converting Data Into Employee Wise Dict
	report_output = {}
	for d in data:
		if not 'employee' in d:
			continue
		report_output[d['employee']] = []
		for col in d:
			if col in ['shift', 'employee', 'employee_name']:
				continue
			d[col].update({
				"employee_name" : d['employee_name']
			})
			report_output[d['employee']].append(d[col])
			
	# Converting Report Data Into Rows By Detail Type
	report_rows = []
	for out in report_output:
		category = frappe.db.get_value("Employee", out, "custom_category") if out != None else ""
		sts_row = {
			'total' : 0,
			'employee':out, 
			'detail': 'Status', 
			'shift' : report_output[out][0]['shift'], 
			'department' :report_output[out][0]['department'], 
			'employee_name':report_output[out][0]['employee_name'], 
			'total_days_present' : 0,
			'total_days_absent' : 0,
			'total_days_on_leave': 0,
			'category': category,
			'total_ot_hours' : 0
		}

		in_row = {
			'hidden_employee':out, 
			# 'employee_name':report_output[out][0]['employee_name'],  
			'detail': 'In Time', 
			'shift' :report_output[out][0]['shift'], 
			'department' :report_output[out][0]['department'], 
			"indent": 1,
			'category': category
		}

		out_row = {
			'hidden_employee':out, 
			'detail': 'Out Time', 
			'shift' : report_output[out][0]['shift'], 
			'department' :report_output[out][0]['department'], 
			"indent": 1,
			'category': category
		}

		hrs_row = {
			'hidden_employee':out, 
			'detail': 'Total Hrs', 
			'shift' : report_output[out][0]['shift'], 
			'department' :report_output[out][0]['department'], 
			'total' : 0, 
			"indent": 1,
			'category': category
		}

		ot_row = {
			'hidden_employee':out, 
			'detail': 'OT Hrs', 
			'shift' : report_output[out][0]['shift'], 
			'department' :report_output[out][0]['department'], 
			"indent": 1,
			'total' : 0	,
			'category': category
		}

		late_checkin_row = {
			'hidden_employee':out, 
			'detail': 'Late Check in By', 
			'shift' : report_output[out][0]['shift'], 
			'department' :report_output[out][0]['department'], 
			"indent": 1,
			'category': category
		}

		early_exit_row = {
			'hidden_employee':out, 
			'detail': 'Early Exit By', 
			'shift' : report_output[out][0]['shift'], 
			'department' :report_output[out][0]['department'], 
			"indent": 1,
			'category': category
		}

		# Adding Days Attendance Time & Status
		day = 1
		for d in report_output[out]:
			# Updating In Time Row
			if d['in_time'] is not None:
				if d['in_time'] != "-":
					in_row[day] = d['in_time'].strftime("%H:%M")
			else:
				in_row[day] = "-" if d['in_time'] is None else d['in_time']
			
			# Updating Out Time Row
			if d['out_time'] is not None:
				if d['out_time'] != "-":
					out_row[day] = d['out_time'].strftime("%H:%M")
			else:
				out_row[day] =  "-" if d['out_time'] is None else d['out_time']

			# Updating Total Hours Row
			total_working_seconds = 0
			if d['working_hours']:
				working_hours = int(d['working_hours'])
				working_minute = (d['working_hours'] - working_hours) * 100
				total_working_seconds = (working_hours * 3600) + (working_minute * 60)
			formatted_duration = frappe.utils.format_duration(total_working_seconds)
			hrs_row[day] = formatted_duration or d['working_hours']
			hrs_row['total'] = round(hrs_row['total'] + d['working_hours'], 2)

			# Updating Status Row
			sts_row[day] = d['status']
			if d['status'] in ["P", "WFH"]:
				sts_row['total'] = sts_row['total'] + 1 
				sts_row['total_days_present'] = sts_row['total_days_present'] + 1 
			elif d['status'] == "HD":
				sts_row['total'] = sts_row['total'] + 0.5
				sts_row['total_days_present'] = sts_row['total_days_present'] + 0.5
			elif d['status'] in ["A", "L"]:
				sts_row['total_days_absent'] = sts_row['total_days_absent'] + 1

			for leave in leaves:
				colname = leave.replace(" ", "_").lower()
				sts_row[colname] = 0
				if employee_leaves_map[d['employee']] != []:
					for l in employee_leaves_map[d['employee']]:
						if l.leave_type == leave:
							sts_row[colname] = l.count
			total_leaves = 0
			if employee_leaves_map[d['employee']] != []:
				for x in employee_leaves_map[d['employee']]:
					total_leaves = total_leaves + x.count
			sts_row['total_days_on_leave'] = total_leaves

			sts_row['total_ot_hours'] = sts_row['total_ot_hours'] + (d['custom_rounded_extra_working_hours'] if 'custom_rounded_extra_working_hours' in d else 0)
			# Updating Over Time Row
			ot_row[day] = d['custom_rounded_extra_working_hours'] if 'custom_rounded_extra_working_hours' in d else 0
			ot_row['total'] = ot_row['total'] + (d['custom_rounded_extra_working_hours'] if 'custom_rounded_extra_working_hours' in d else 0)

			# Updating Late CheckIn Row
			if d['late_entry'] == 1:
				start_time = frappe.db.get_value("Shift Type", d['shift'], 'start_time')
				time_difference = frappe.utils.time_diff(str(d['in_time']), f"{attendance_year}-{attendance_month}-{day} {start_time}")
				late_checkin_row[day] = time_difference
			else:
				late_checkin_row[day] = "-"

			# Updating Early Exit Row
			if d['early_exit'] == 1:
				end_time = frappe.db.get_value("Shift Type", d['shift'], 'end_time')
				time_difference = frappe.utils.time_diff(f"{attendance_year}-{attendance_month}-{day} {end_time}", str(d['out_time']))
				early_exit_row[day] = time_difference
			else:
				early_exit_row[day] = "-"

			# Moving to Next Day
			day = day + 1

		# Appending Rows In Final Data
		report_rows.append(sts_row)
		report_rows.append(in_row)
		report_rows.append(out_row)
		report_rows.append(hrs_row)
		report_rows.append(ot_row)
		report_rows.append(late_checkin_row)
		report_rows.append(early_exit_row)
	
	# If Filters Applied Then Fileter Data As Per Applied Filters
	if filters:
		keys = list(filters.keys())
		if keys == ['from_date', 'to_date']:
			return report_rows
		report_rows = get_filtered_data(filters, report_rows)

	# Return Final Data
	return report_rows