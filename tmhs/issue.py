"""Issue (Support Ticket) customizations for TMHS.

- moves `customer` / `raised_by` out of the entry form into the Reference section
- adds a Followers tab; followers get a notification on new comments and on status change
"""

import json

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

# standard Issue field order with customer/raised_by moved into the "Reference" (additional_info) section
FIELD_ORDER = [
	"subject_section", "naming_series", "subject", "cb00", "status", "priority", "issue_type",
	"issue_split_from", "sb_details", "description", "service_level_section",
	"service_level_agreement", "response_by", "reset_service_level_agreement", "cb",
	"agreement_status", "sla_resolution_by", "service_level_agreement_creation", "on_hold_since",
	"total_hold_time", "response", "first_response_time", "first_responded_on", "column_break_26",
	"avg_response_time", "section_break_19", "resolution_details", "column_break1", "opening_date",
	"opening_time", "sla_resolution_date", "resolution_time", "user_resolution_time",
	"additional_info", "customer", "raised_by", "lead", "contact", "email_account",
	"column_break_16", "customer_name", "project", "company", "via_customer_portal", "attachment",
	"content_type",
]


def setup():
	"""Idempotent; run by patch and after_migrate."""
	frappe.db.delete("Property Setter", {"doc_type": "Issue", "doctype_or_field": "DocType", "property": "field_order"})
	make_property_setter(
		"Issue", None, "field_order", json.dumps(FIELD_ORDER), "Text",
		for_doctype=True, validate_fields_for_doctype=False,
	)
	create_custom_fields(
		{
			"Issue": [
				{
					"fieldname": "followers_tab",
					"label": "Followers",
					"fieldtype": "Tab Break",
					"insert_after": "content_type",
				},
				{
					"fieldname": "followers",
					"label": "Followers",
					"fieldtype": "Table MultiSelect",
					"options": "User Group Member",
					"description": _("These users are notified on new comments and status changes."),
					"insert_after": "followers_tab",
				},
			]
		},
		update=True,
	)
	frappe.clear_cache(doctype="Issue")


def on_update(doc, method=None):
	"""Issue.on_update — notify followers when the status changes."""
	if doc.has_value_changed("status"):
		notify_followers(doc, _("Issue {0} is now {1}").format(doc.name, _(doc.status)), doc.subject)


def on_comment(doc, method=None):
	"""Comment.after_insert — notify followers of a new comment on an Issue."""
	if doc.comment_type == "Comment" and doc.reference_doctype == "Issue":
		subject = _("New comment on Issue {0}").format(doc.reference_name)
		notify_followers(frappe.get_doc("Issue", doc.reference_name), subject, doc.content)


def notify_followers(issue, subject, content=None):
	users = {f.user for f in issue.get("followers") or []} - {frappe.session.user}
	if not users:
		return

	enqueue_create_notification(
		list(users),
		{
			"type": "Alert",
			"document_type": "Issue",
			"document_name": issue.name,
			"subject": subject,
			"email_content": content,
			"from_user": frappe.session.user,
		},
	)
