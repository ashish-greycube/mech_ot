import frappe
from frappe import _
from frappe.utils import flt, cstr, add_to_date, time_diff_in_seconds, get_datetime, formatdate, get_link_to_form


def calculate_ot_hours_and_amount(doc, method):
    """Calculate Overtime Hours and Amount for Attendance Document"""
    eligible_for_ot = frappe.db.get_value("Employee", doc.employee, "custom_is_ot_applicable")

    # if doc.employee == "10483":
    if not doc.custom_rounded_extra_working_hours:
        doc.custom_rounded_extra_working_hours = 0.0

    if not doc.custom_overtime_amount:
        doc.custom_overtime_amount = 0.0

    # Fetch Actual Working Hours and Shift End Time from Shift Type
    shift_type = frappe.get_doc("Shift Type", doc.shift)
    actual_working_hours = shift_type.custom_shift_actual_working_hours or 0.0
    shift_end_time = shift_type.end_time

    doc.custom_difference_of_working_hours = flt(doc.working_hours) - flt(actual_working_hours)

    # Calculate Overtime Hours
    if eligible_for_ot and doc.working_hours and doc.working_hours > actual_working_hours:
        if doc.out_time and shift_end_time:
            out_time = get_datetime(doc.out_time)
            shift_end_datetime = get_datetime(cstr((doc.attendance_date)) + " " + cstr(shift_end_time))
            minimum_duration_for_overtime = frappe.db.get_value("Shift Type",doc.shift,"custom_minimum_duration_for_overtime") or 0
            end_time_allowed_for_overtime = add_to_date(shift_end_datetime,minutes=minimum_duration_for_overtime)
            print(end_time_allowed_for_overtime,"-----------",shift_end_datetime)

            rounding_min_threshold_for_05_hr = frappe.db.get_single_value("Mech OT Settings", "rounding_min_threshold_for_05_hr") or 0
            rounding_min_threshold_for_1_hr = frappe.db.get_single_value("Mech OT Settings", "rounding_min_threshold_for_1_hr") or 0

            if rounding_min_threshold_for_05_hr == 0 or rounding_min_threshold_for_1_hr == 0:
                frappe.throw(_("Please set Rounding Thresholds in {0}".format(get_link_to_form("Mech OT Settings","Mech OT Settings"))))

            if out_time >= end_time_allowed_for_overtime:
                overtime_duration = time_diff_in_seconds(out_time , shift_end_datetime)
                doc.custom_actual_extra_working_hours = flt(overtime_duration) / 3600
                working_hours, remaining_working_seconds = divmod(overtime_duration, 3600)
                remaining_working_minutes = remaining_working_seconds / 60

                if remaining_working_minutes > rounding_min_threshold_for_05_hr and remaining_working_minutes <= rounding_min_threshold_for_1_hr:
                    working_hours += 0.5
                elif remaining_working_minutes > rounding_min_threshold_for_1_hr:
                    working_hours += 1
                
                doc.custom_rounded_extra_working_hours = flt(working_hours,2)
            else:
                doc.custom_rounded_extra_working_hours = 0.0
        else:
            doc.custom_rounded_extra_working_hours = 0.0

        # Fetch Salary Structure Assignment to get Gross Pay
        ssa = frappe.get_all(
            "Salary Structure Assignment",
            filters={"employee": doc.employee,"docstatus":1},
            fields=["custom_gross_pay"],
            limit_page_length=1,
            order_by="from_date desc"
        )
        
        gross_pay = ssa[0].custom_gross_pay if len(ssa)>0 else 0.0

        # Calculate Overtime Amount
        month_last_day = frappe.utils.get_last_day(doc.attendance_date).day
        multiplication_factor_for_ot = frappe.db.get_single_value("Mech OT Settings", "multiplication_factor") or 0
        ot_rate = gross_pay / month_last_day / actual_working_hours * multiplication_factor_for_ot
        ot_amount = doc.custom_rounded_extra_working_hours * ot_rate

        doc.custom_overtime_rate = ot_rate
        doc.custom_overtime_amount = ot_amount