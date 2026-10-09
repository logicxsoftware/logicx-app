import frappe


def check_app_permission():
	if frappe.session.user == "Administrator":
		return True

	return frappe.has_permission("LogicX Product", ptype="read")
