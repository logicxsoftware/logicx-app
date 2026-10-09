import frappe
from frappe.tests import IntegrationTestCase

from logicx_app.logicx.doctype.logicx_product.logicx_product import (
	_stock_default,
	create_new_product,
	link_existing_item,
)

IGNORE_TEST_RECORD_DEPENDENCIES = ["Item", "Item Group"]
test_records = {}


class TestLogicXProduct(IntegrationTestCase):
	def test_create_new_product_creates_and_links_item(self):
		product_name = f"LogicX Test {frappe.generate_hash(length=8)}"
		product = create_new_product(
			{
				"product_name": product_name,
				"short_description": "Created from LogicX",
				"description": "A catalog test product.",
				"enabled": 1,
				"price": 125,
			}
		)

		item = frappe.get_doc("Item", product["item"])
		self.assertEqual(item.item_name, product_name)
		self.assertEqual(item.standard_rate, 125)
		self.assertEqual(product["item_source"], "Created by LogicX")
		self.assertTrue(frappe.db.exists("LogicX Product", product["name"]))

	def test_link_existing_item_keeps_item_unchanged(self):
		item_code = f"LOGIX-LINK-{frappe.generate_hash(length=8)}"
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": "Existing ERPNext Item",
				"item_group": _stock_default("item_group", "Item Group", {"is_group": 0}),
				"stock_uom": _stock_default("stock_uom", "UOM"),
				"description": "ERPNext-owned description",
				"standard_rate": 75,
			}
		).insert()

		product = link_existing_item(
			item.name,
			{"product_name": "Catalog title", "description": "Catalog description", "enabled": 0},
		)
		item.reload()

		self.assertEqual(product["item"], item.name)
		self.assertEqual(product["item_source"], "Linked from ERPNext")
		self.assertEqual(item.description, "ERPNext-owned description")
		self.assertEqual(item.standard_rate, 75)
