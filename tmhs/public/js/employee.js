// Copyright (c) 2026, James Meshack and contributors
// For license information, please see license.txt

// Everything the certificate needs is checked here rather than server-side, so
// a missing field arrives as a dialog naming the record to fix instead of a
// 417 from the download endpoint.

function missing_on_employee(frm) {
	return [
		[frm.doc.designation, __("Designation")],
		[frm.doc.date_of_joining, __("Date of Joining")],
	]
		.filter(([value]) => !value)
		.map(([, label]) => label);
}

frappe.ui.form.on("Employee", {
	refresh(frm) {
		if (frm.is_new() || !frappe.user.has_role(["HR Manager", "HR User"])) return;

		frm.add_custom_button(__("Download Certificate of Service"), () => {
			const missing = missing_on_employee(frm);
			if (missing.length) {
				frappe.msgprint({
					title: __("Certificate of Service"),
					indicator: "orange",
					message: __("Set {0} on {1} before printing the certificate.", [
						frappe.utils.comma_and(missing),
						frm.doc.employee_name.bold(),
					]),
				});
				return;
			}

			frappe.prompt(
				[
					{
						label: __("Director"),
						fieldname: "director",
						fieldtype: "Link",
						options: "User",
						reqd: 1,
						description: __("Whose name signs the certificate."),
					},
					{
						// The User doctype has no job title and almost no user
						// here is linked to an Employee record, so the title is
						// typed rather than looked up. It rarely changes.
						label: __("Title"),
						fieldname: "title",
						fieldtype: "Data",
						reqd: 1,
						default: "Director of HR & Administration",
						description: __("Printed under their name."),
					},
				],
				({ director, title }) =>
					window.open(
						frappe.urllib.get_full_url(
							"/api/method/tmhs.certificate_of_service.download" +
								`?employee=${encodeURIComponent(frm.doc.name)}` +
								`&director=${encodeURIComponent(director)}` +
								`&title=${encodeURIComponent(title)}`
						)
					),
				__("Certificate of Service"),
				__("Download")
			);
		});
	},
});
