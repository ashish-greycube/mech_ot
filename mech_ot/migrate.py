import frappe
def after_migrate():
    custom_fields = {
        "Holiday List" : [
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Column Break",
                fieldname="custom_weekoff_columns",
                insert_after="get_weekly_off_dates"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Select",
                label="Mech Weekly Off",
                fieldname="custom_mech_weekoff",
                options="\nOdd Saturdays (1st-3rd-5th)\nEven Saturdays (2nd-4th)",
                insert_after="custom_weekoff_columns"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Button",
                label="Add to Holidays",
                fieldname="custom_add_holidays_btn",
                insert_after="custom_mech_weekoff"
            ),
        ], 

        "Leave Type" : [
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Data",
                label="Abbreviation",
                fieldname="custom_abbreviation",
                insert_after="max_continuous_days_allowed",
                reqd=1
            ),
        ],

        "Employee": [
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Check",
                label="Is OT applicable?",
                fieldname="custom_is_ot_applicable",
                insert_after="provident_fund_account"
            ),
        ],

        "Shift Type": [
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Float",
                label="Shift Actual Working Hours",
                fieldname="custom_shift_actual_working_hours",
                precision=2,
                insert_after="end_time",
                description="For Overtime Calculation"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Float",
                label="Minimum Duration For Overtime",
                fieldname="custom_minimum_duration_for_overtime",
                precision=2,
                insert_after="custom_shift_actual_working_hours",
                description="In Minutes"
            ),
        ],

        "Salary Structure Assignment": [
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Currency",
                label="Gross Pay",
                fieldname="custom_gross_pay",
                precision=2,
                allow_on_submit=1,
                insert_after="currency"
            ),
        ],

        "Attendance": [
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Section Break",
                label="Overtime Details",
                fieldname="custom_overtime_details",
                insert_after="half_day_status"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Float",
                label="Difference of Working Hours",
                fieldname="custom_difference_of_working_hours",
                read_only=1,
                insert_after="custom_overtime_details",
                description="Working Hours - Shift Actual Working Hours"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Float",
                label="Actual Extra Working Hours",
                fieldname="custom_actual_extra_working_hours",
                read_only=1,
                insert_after="custom_difference_of_working_hours",
                description="Out Time - Shift End Time"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Float",
                label="Rounded Extra Working Hours",
                fieldname="custom_rounded_extra_working_hours",
                read_only=1,
                insert_after="custom_actual_extra_working_hours",
                description="Rounding of Actual Extra Working Hours"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Column Break",
                label="",
                fieldname="custom_column_break_fygem",
                insert_after="custom_rounded_extra_working_hours"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Currency",
                label="Overtime Rate",
                fieldname="custom_overtime_rate",
                read_only=1,
                insert_after="custom_column_break_fygem"
            ),
            dict(
                is_custom_field=1,
                is_system_generated=0,
                fieldtype="Currency",
                label="Overtime Amount",
                fieldname="custom_overtime_amount",
                read_only=1,
                insert_after="custom_overtime_rate"
            ),
        ]  
    }

    print("Adding Custom Fields In Holiday List.....")
    for dt, fields in custom_fields.items():
        print("********************\n %s: " % dt, [d.get("fieldname") for d in fields])
    frappe.custom.doctype.custom_field.custom_field.create_custom_fields(custom_fields)