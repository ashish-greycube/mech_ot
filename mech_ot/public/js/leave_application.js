frappe.ui.form.on("Leave Application", {
    leave_type: function (frm) {
        frappe.db.get_single_value("Mech Attendance Settings", "default_short_leave_type")
            .then((res) => {
                if (res) {
                    if (frm.doc.leave_type == res) {
                        cur_frm.set_value("half_day", 1)
                        cur_frm.set_value("total_leave_days", 0.5)
                        cur_frm.set_df_property("half_day", "read_only", 1)
                    }
                }
            })
    }
})