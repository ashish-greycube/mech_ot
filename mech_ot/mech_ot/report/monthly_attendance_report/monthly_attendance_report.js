// Copyright (c) 2026, GreyCube Technologies and contributors
// For license information, please see license.txt

var date = new Date()
function daysInMonth(year, month) {
	const daysInMonths = [31, (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
	if (month == 12) {
		return daysInMonths[0]
	}
	return daysInMonths[month];
}
frappe.query_reports["Monthly Attendance Report"] = {
	"filters": [
		{
			fieldname: 'from_date',
			fieldtype: 'Date',
			label: __('From Date'),
			default: new Date(date.getFullYear(), date.getMonth(), 1),
			on_change: function () {
				date = new Date(frappe.query_report.get_filter_value("from_date"));
				days = daysInMonth(date.getFullYear(), date.getMonth())
				to_date = frappe.datetime.add_days(date, days - 1)
				frappe.query_report.set_filter_value("to_date", to_date)
				frappe.query_report.refresh()
			}
		},
		{
			fieldname: 'to_date',
			fieldtype: 'Date',
			label: __('To Date'),
			default: frappe.datetime.get_today(),
			on_change: function () {
				date = new Date(frappe.query_report.get_filter_value("to_date"));
				days = daysInMonth(date.getFullYear(), date.getMonth())
				from_date = frappe.datetime.add_days(date, -(days - 1))
				frappe.query_report.set_filter_value("from_date", from_date)
				frappe.query_report.refresh()
			}
		},
		{
			fieldname: 'employee',
			fieldtype: 'Link',
			label: __('Employee'),
			options: 'Employee'
		},
		{
			fieldname: 'shift',
			fieldtype: 'Link',
			label: __('Shift'),
			options: 'Shift Type'
		},
		{
			fieldname: 'department',
			fieldtype: 'Link',
			label: __('Department'),
			options: 'Department'
		},
		{
			fieldname: 'category',
			fieldtype: 'Select',
			label: __('Category'),
			options: '\nStaff\nWorker'
		},
	],

	formatter: function (value, row, column, data, default_formatter, filter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "employee") {
			value = value.bold()
		}
		if (value && value == "P") {
			value = `<span style="color:green;">${value}</span>`
		} else if (value && value == "A") {
			value = `<span style="color:red;">${value}</span>`
		}
		else if (value && ["H", "WO"].includes(value)) {
			value = `<span style="color:orange;">${value}</span>`
		}
		return value;
	},
};
