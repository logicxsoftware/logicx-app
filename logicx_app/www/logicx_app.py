import frappe
from frappe import _
from frappe.translate import get_messages_for_boot
from frappe.utils import get_system_timezone

from logicx_app.api import check_app_permission

no_cache = 1


def get_context():
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/logicx-app"
		raise frappe.Redirect

	if not check_app_permission():
		frappe.throw(_("You do not have permission to access LogicX"), frappe.PermissionError)

	boot = get_boot()
	return {"boot": boot, "csrf_token": boot.csrf_token}


def get_boot():
	system_timezone = get_system_timezone()
	return frappe._dict(
		{
			"site_name": frappe.local.site,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"user": frappe.session.user,
			"translated_messages": get_messages_for_boot(),
			"timezone": {
				"system": system_timezone,
				"user": frappe.db.get_value("User", frappe.session.user, "time_zone")
				or system_timezone,
			},
		}
	)
