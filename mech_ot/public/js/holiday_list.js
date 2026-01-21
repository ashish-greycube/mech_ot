frappe.ui.form.on("Holiday List", {
    custom_add_holidays_btn: function (frm) {
        if (frm.is_new()) {
            frappe.throw("Please <b>Save</b> Form To Add Custom Holidays..")
        }
        if (frm.doc.custom_mech_weekoff == undefined || frm.doc.custom_mech_weekoff == "") {
            frappe.throw("Please Select <b>Week Off Type</b> To Add Custom Holidays..")
        }
        frappe.call({
            method: "mech_ot.api.add_saturday_weekoffs",
            args: {
                "holiday_list": frm.doc.name,
                "holiday_type": frm.doc.custom_mech_weekoff,
                "start_date": frm.doc.from_date,
                "end_date": frm.doc.to_date,
            },
            callback: function (res) {
                frappe.show_alert({ message: `${frm.doc.custom_mech_weekoff} Added In Holidays!`, indicator: "green" })
                cur_frm.reload_doc();
            }
        })
    }
});