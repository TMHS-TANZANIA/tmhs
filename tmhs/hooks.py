app_name = "tmhs"
app_title = "Tmhs"
app_publisher = "James Meshack"
app_description = "TMHS Group specific customization for erpnext and other modules, this app is use as the app for performing the decoupling of the current edits on the erpnext core"
app_email = "system@tmhsgroup.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "tmhs",
# 		"logo": "/assets/tmhs/logo.png",
# 		"title": "Tmhs",
# 		"route": "/tmhs",
# 		"has_permission": "tmhs.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tmhs/css/tmhs.css"
# app_include_js = "/assets/tmhs/js/tmhs.js"

# include js, css files in header of web template
# web_include_css = "/assets/tmhs/css/tmhs.css"
# web_include_js = "/assets/tmhs/js/tmhs.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tmhs/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Employee": "public/js/employee.js","Material Request": "public/js/material_request.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "tmhs/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "tmhs.utils.jinja_methods",
# 	"filters": "tmhs.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tmhs.install.before_install"
# after_install = "tmhs.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tmhs.uninstall.before_uninstall"
# after_uninstall = "tmhs.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "tmhs.utils.before_app_install"
# after_app_install = "tmhs.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "tmhs.utils.before_app_uninstall"
# after_app_uninstall = "tmhs.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tmhs.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tmhs.tasks.all"
# 	],
# 	"daily": [
# 		"tmhs.tasks.daily"
# 	],
# 	"hourly": [
# 		"tmhs.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tmhs.tasks.weekly"
# 	],
# 	"monthly": [
# 		"tmhs.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "tmhs.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tmhs.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "tmhs.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tmhs.utils.before_request"]
# after_request = ["tmhs.utils.after_request"]

# Job Events
# ----------
# before_job = ["tmhs.utils.before_job"]
# after_job = ["tmhs.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"tmhs.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

