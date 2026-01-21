import frappe
import calendar
from frappe import _
from datetime import timedelta
from dateutil import relativedelta
from frappe.utils import flt, cstr, add_to_date, time_diff_in_seconds, get_datetime, formatdate, get_link_to_form, getdate
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

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

# ----------------------- Compensantory Leave Off Feature -------------------------
def get_holiday_list_for_employee(employee, shift, company):
    '''
    Returns Holiday List Of Employee;
    Priority: Employee > Shift Type > Company
    '''
    employee_holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
    if not employee_holiday_list:
        employee_holiday_list = frappe.db.get_value("Shift Type", shift, "holiday_list")
        if not employee_holiday_list: 
            employee_holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")
    return employee_holiday_list

def create_compensatory_leave_for_elgible_employees_attendance(self, method=None):
    settings = frappe.get_doc("Mech Attendance Settings")
    if self.employee and self.attendance_date and self.status == "Present":
        employee_holiday_list = get_holiday_list_for_employee(self.employee, self.shift, self.company)

        is_holiday_attendance = is_holiday(employee_holiday_list, self.attendance_date)
        if is_holiday_attendance: 
            mark_auto_attendance_on_holidays = frappe.db.get_value("Shift Type", self.shift, "mark_auto_attendance_on_holidays")
            employee_category = frappe.db.get_value("Employee", self.employee, "custom_category")

            if mark_auto_attendance_on_holidays == 1 and employee_category == settings.employee_category:
                new_compensatory_leave_balance = 0
                if self.working_hours and self.working_hours >= settings.minimum_hours_required_for_half_day_compensatory_off and self.working_hours < settings.minimum_hours_required_for_full_day_compensatory_off:
                    new_compensatory_leave_balance = 0.5
                elif self.working_hours and self.working_hours >= settings.minimum_hours_required_for_full_day_compensatory_off:
                    new_compensatory_leave_balance = 1

                if new_compensatory_leave_balance > 0:
                    compensatory_doc = frappe.new_doc("Compensatory Leave Request")
                    compensatory_doc.employee = self.employee
                    compensatory_doc.department = self.department
                    compensatory_doc.work_from_date = self.attendance_date
                    compensatory_doc.work_end_date = self.attendance_date
                    compensatory_doc.leave_type = settings.default_compensatory_off_leave_type
                    compensatory_doc.reason = "Worked On Holiday\nDetails:\nAttendance: {0}\nWorking Hours: {1}".format(self.name, self.working_hours)

                    compensatory_doc.save(ignore_permissions=True)
                    compensatory_doc.submit()
                    frappe.msgprint("Compensatory Leave Request Is Created {0}".format(get_link_to_form("Compensatory Leave Request", compensatory_doc.name)))

@frappe.whitelist()
def add_saturday_weekoffs(holiday_list, holiday_type, start_date, end_date):
    self = frappe.get_doc("Holiday List", holiday_list)
    start_date, end_date = getdate(start_date), getdate(end_date)
    
    existing_date_list = [getdate(holiday.holiday_date) for holiday in self.get("holidays")]
    if holiday_type == "Odd Saturdays (1st-3rd-5th)":
        odd_saturdays = get_odd_saturdays(start_date, end_date, existing_date_list)
        if len(odd_saturdays) > 0:
            for saturday in odd_saturdays:
                self.append("holidays", {
                    "holiday_date": saturday,
                    "weekly_off": 1,
                    "description": "Odd Saturday[1st/3rd/5th]"
                })
    elif holiday_type == "Even Saturdays (2nd-4th)":
        even_saturdays = get_even_saturdays(start_date, end_date, existing_date_list)
        if len(even_saturdays) > 0:
            for saturday in even_saturdays:
                self.append("holidays", {
                    "holiday_date": saturday,
                    "weekly_off": 1,
                    "description": "Even Saturday[2nd/4th]"
                })
    self.save(ignore_permissions=True)
        
def get_odd_saturdays(start_date, end_date, existing_date_list):
    date_list = []
    reference_date = start_date + relativedelta.relativedelta(weekday=calendar.SATURDAY)
    while reference_date <= end_date:
        ordinal = (reference_date.day - 1) // 7 + 1
        if ordinal % 2 != 0:
            if reference_date not in existing_date_list:
                date_list.append(reference_date)
        reference_date += timedelta(days=7)
    return date_list

def get_even_saturdays(start_date, end_date, existing_date_list):
    date_list = []
    reference_date = start_date + relativedelta.relativedelta(weekday=calendar.SATURDAY)
    while reference_date <= end_date:
        ordinal = (reference_date.day - 1) // 7 + 1
        if ordinal % 2 == 0:
            if reference_date not in existing_date_list:
                date_list.append(reference_date)
        reference_date += timedelta(days=7)
    return date_list