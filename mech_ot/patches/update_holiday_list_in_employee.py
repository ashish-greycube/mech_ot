import frappe
from frappe import _

def execute():
    holiday_list_assignment_records = frappe.get_all(
        "Holiday List Assignment",
        filters={"applicable_for": "Employee", "holiday_list": ("!=", "")},
        fields=["name","holiday_list", "assigned_to"],
    )

    if len(holiday_list_assignment_records) > 0:
        for record in holiday_list_assignment_records:
            frappe.db.set_value(
                "Employee",
                record.assigned_to,
                "custom_assigned_holiday_list",
                record.holiday_list
            )
        frappe.msgprint(_("Assigned Holiday List is updated in employee profiles"), alert=True)
        print("Assigned Holiday List is updated in employee profiles")