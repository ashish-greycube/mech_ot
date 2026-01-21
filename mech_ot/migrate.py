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
        ]
    }

    print("Adding Custom Fields In Holiday List.....")
    for dt, fields in custom_fields.items():
        print("********************\n %s: " % dt, [d.get("fieldname") for d in fields])
    frappe.custom.doctype.custom_field.custom_field.create_custom_fields(custom_fields)