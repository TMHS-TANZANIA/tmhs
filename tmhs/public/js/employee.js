// Copyright (c) 2026, James Meshack and contributors
// For license information, please see license.txt

// Everything the certificate needs is checked here rather than server-side, so
// a missing field arrives as a dialog naming the record to fix instead of a
// 417 from the download endpoint.

function tell(message) {
	frappe.msgprint({
		title: __("Certificate of Service"),
		indicator: "orange",
		message: message,
	});
}

// From/To default to the employee's contract period; both stay editable, since
// an employee hired before any of this was in the system has neither a Contract
// nor a Job Offer to read them off.
async function service_period(employee) {
	const { message } = await frappe.call({
		method: "tmhs.certificate_of_service.service_period",
		args: { employee: employee },
	});
	return message || {};
}

frappe.ui.form.on("Employee", {
	refresh(frm) {
		if (frm.is_new() || !frappe.user.has_role(["HR Manager", "HR User"])) return;

		frm.add_custom_button(__("Download Certificate of Service"), async () => {
			if (!frm.doc.designation) {
				tell(
					__("Set a Designation on {0} before printing the certificate.", [
						frm.doc.employee_name.bold(),
					]) +
						"<br><br>" +
						__("It is printed as the position they served in.")
				);
				return;
			}

			const period = await service_period(frm.doc.name);

			frappe.prompt(
				[
					{
						label: __("From"),
						fieldname: "from_date",
						fieldtype: "Date",
						reqd: 1,
						default: period.from_date,
					},
					{
						label: __("To"),
						fieldname: "to_date",
						fieldtype: "Date",
						reqd: 1,
						default: period.to_date,
					},
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
				({ from_date, to_date, director, title }) => {
					if (frappe.datetime.get_diff(to_date, from_date) < 0) {
						tell(__("To cannot be earlier than From."));
						return;
					}

					window.open(
						frappe.urllib.get_full_url(
							"/api/method/tmhs.certificate_of_service.download" +
								`?employee=${encodeURIComponent(frm.doc.name)}` +
								`&director=${encodeURIComponent(director)}` +
								`&title=${encodeURIComponent(title)}` +
								`&from_date=${encodeURIComponent(from_date)}` +
								`&to_date=${encodeURIComponent(to_date)}`
						)
					);
				},
				__("Certificate of Service"),
				__("Download")
			);
		});
	},
});
