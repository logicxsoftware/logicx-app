app_name = "logicx_app"
app_title = "LogicX"
app_publisher = "CODEXSUN"
app_description = "LogicX application foundation for Frappe and ERPNext"
app_email = ""
app_license = "mit"
app_icon = "shopping-cart"
app_color = "#172554"
app_logo_url = "/assets/logicx_app/images/logicx-logo.svg?v=3"
app_home = "/logicx-app"

required_apps = ["erpnext"]

after_install = "logicx_app.install.after_install"

add_to_apps_screen = [
	{
		"name": app_name,
		"logo": app_logo_url,
		"title": app_title,
		"route": app_home,
	}
]

website_route_rules = [
	{"from_route": "/logicx-app", "to_route": "logicx_app"},
	{"from_route": "/logicx-app/<path:app_path>", "to_route": "logicx_app"},
]
