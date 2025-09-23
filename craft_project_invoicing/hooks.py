from . import __version__ as app_version

app_name = "craft_project_invoicing"
app_title = "Craft Project Invoicing"
app_publisher = "craftinteractive.ae"
app_description = "craft_project_invoicing"
app_email = "craftinteractive.ae"
app_license = "MIT"

# Includes in <head>
# ------------------
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["name", "in",
					 (
						 # Sales Invoice
						 "Sales Invoice-ref_journal_entry",
						 "Sales Invoice-sales_order",
						 "Sales Invoice-custom_invoice_percentage",
						 "Sales Invoice-custom_sales_order_type",
                         "Sales Invoice-custom_proforma_invoice_ref",
                         "Sales Invoice-custom_advance_percentage",
                         "Sales Invoice-custom_expected_collected_date",

						 # Sales Invoice Item
						 "Sales Invoice Item-custom_so_qty",
                         "Sales Invoice Item-custom_section_break_hdgti",
                         "Sales Invoice Item-custom_cumulative",
                         "Sales Invoice Item-custom_invoicing_percentage",
                         "Sales Invoice Item-custom_previous",
                         "Sales Invoice Item-custom_column_break_n5gct",
                         "Sales Invoice Item-custom_cumulative_percentage",
                         "Sales Invoice Item-custom_previous_invoicing_",
						 "Sales Invoice Item-custom_column_break_8v7u9",
                         "Sales Invoice Item-custom_retention_details",
                         "Sales Invoice Item-custom_previous_balance_amount_ret",
                         "Sales Invoice Item-custom_previous_retention_amount",
						 "Sales Invoice Item-custom_cumulative_retention",
                         "Sales Invoice Item-custom_previous_advance_amount",
                         "Sales Invoice Item-custom_previous_balance_amount_ad",
                         "Sales Invoice Item-custom_cumulative_advance",
                         "Sales Invoice Item-custom_column_break_vv9z9",
                         "Sales Invoice Item-custom_balance_amount_ret",
                         "Sales Invoice Item-custom_balance_amount_ad",
                         "Sales Invoice Item-custom_retention_",
                         "Sales Invoice Item-custom_advance_amount",
                         "Sales Invoice Item-custom_retention_amount",
                         "Sales Invoice Item-custom_advance_",
                         "Sales Invoice Item-custom_section_break_ohveg",
                         
						 #Sales Taxes and Charges
                         
						 "Sales Taxes and Charges-custom_cumulative_amount",
                         "Sales Taxes and Charges-custom_previous_amount",

						 # Sales Order
						 "Sales Order-custom_order_invoicing_type",
						 "Sales Order-custom_section_break_sfox3",
						 "Sales Order-consumed_advance",
						 "Sales Order-consumed_retention",
						 "Sales Order-custom_section_break_jslmq",
						 "Sales Order-enable_project_invoicing",
						 "Sales Order-section_break_kyki6",
						 "Sales Order-section_break_gxjur",
						 "Sales Order-advance_percentage",
						 "Sales Order-on_delivery_percentage",
						 "Sales Order-column_break_mdvgl",
						 "Sales Order-retention_percentage",
						 "Sales Order-advance_billed_amount",
						 "Sales Order-retention_billed_amount",
						 "Sales Order-delivery_billed_amount",
						 "Sales Order-advance_billed",
						 "Sales Order-on_delivery_billed",
						 "Sales Order-retention_billed",
						 "Sales Order-advance_ref_doc",
						 "Sales Order-delivery_ref_doc",
						 "Sales Order-retention_ref_doc",

						 # Company
						 "Company-project_invoicing_configuration",
						 "Company-project_invoicing_tax_template",
						 # Sales Taxes and Charges
						 "Sales Taxes and Charges-is_advance",
						 "Sales Taxes and Charges-is_retention",
					 )
			 ]
		]
	},
	{
		"dt": "Property Setter",
		"filters": [
			["name", "in",
			# [
			# 	# Journal Entry Account
			# 	"Journal Entry Account-reference_type-options",
			# ]
            (
                "Sales Invoice Item-qty-columns",
                "Sales Invoice Item-item_code-columns",
                "Sales Invoice Item-main-field_order",
                "Sales Taxes and Charges-main-field_order",
                "Sales Invoice Item-main-field_order",
			)
			]
		]
	},
]
# include js, css files in header of desk.html
# app_include_css = "/assets/craft_project_invoicing/css/craft_project_invoicing.css"
# app_include_js = "/assets/craft_project_invoicing/js/craft_project_invoicing.js"

# include js, css files in header of web template
# web_include_css = "/assets/craft_project_invoicing/css/craft_project_invoicing.css"
# web_include_js = "/assets/craft_project_invoicing/js/craft_project_invoicing.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "craft_project_invoicing/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js",
	"Sales Order": "public/js/sales_order.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# "methods": "craft_project_invoicing.utils.jinja_methods",
# "filters": "craft_project_invoicing.utils.jinja_filters"
# }

# Installation
# ------------
after_install = "craft_project_invoicing.setup.install.after_install"
# before_install = "craft_project_invoicing.install.before_install"
# after_install = "craft_project_invoicing.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "craft_project_invoicing.uninstall.before_uninstall"
# after_uninstall = "craft_project_invoicing.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "craft_project_invoicing.utils.before_app_install"
# after_app_install = "craft_project_invoicing.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "craft_project_invoicing.utils.before_app_uninstall"
# after_app_uninstall = "craft_project_invoicing.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "craft_project_invoicing.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Order": {
		"validate": "craft_project_invoicing.events.sales_order.validate",
	},
	"Sales Invoice": {
		"on_submit": "craft_project_invoicing.events.sales_invoice.on_submit",
		"on_cancel": "craft_project_invoicing.events.sales_invoice.on_cancel",
        "validate": "craft_project_invoicing.events.sales_invoice.validate",

	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# "all": [
# "craft_project_invoicing.tasks.all"
# ],
# "daily": [
# "craft_project_invoicing.tasks.daily"
# ],
# "hourly": [
# "craft_project_invoicing.tasks.hourly"
# ],
# "weekly": [
# "craft_project_invoicing.tasks.weekly"
# ],
# "monthly": [
# "craft_project_invoicing.tasks.monthly"
# ],
# }

# Testing
# -------

# before_tests = "craft_project_invoicing.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# "frappe.desk.doctype.event.event.get_events": "craft_project_invoicing.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# "Task": "craft_project_invoicing.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["craft_project_invoicing.utils.before_request"]
# after_request = ["craft_project_invoicing.utils.after_request"]

# Job Events
# ----------
# before_job = ["craft_project_invoicing.utils.before_job"]
# after_job = ["craft_project_invoicing.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# {
# "doctype": "{doctype_1}",
# "filter_by": "{filter_by}",
# "redact_fields": ["{field_1}", "{field_2}"],
# "partial": 1,
# },
# {
# "doctype": "{doctype_2}",
# "filter_by": "{filter_by}",
# "partial": 1,
# },
# {
# "doctype": "{doctype_3}",
# "strict": False,
# },
# {
# "doctype": "{doctype_4}"
# }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# "craft_project_invoicing.auth.validate"
# ]
