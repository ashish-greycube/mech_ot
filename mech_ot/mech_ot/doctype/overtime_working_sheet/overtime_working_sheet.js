// Copyright (c) 2025, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Working Sheet", {
	fetch_employee(frm) {
        frm.call("fetch_employee").then( r => {
            console.log(r.message)
        })
	},
});
