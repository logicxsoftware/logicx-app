import frappe
from frappe.utils.install import auto_generate_icons_and_sidebar

APP_NAME = "logicx_app"
APP_LOGO_URL = "/assets/logicx_app/images/logicx-logo.svg?v=3"


def after_install():
	auto_generate_icons_and_sidebar(APP_NAME)
	update_desktop_icon_logo()


def update_desktop_icon_logo():
	icon_name = frappe.db.get_value(
		"Desktop Icon",
		{"app": APP_NAME, "icon_type": "App"},
	)
	if icon_name:
		frappe.db.set_value(
			"Desktop Icon",
			icon_name,
			"logo_url",
			APP_LOGO_URL,
			update_modified=False,
		)
