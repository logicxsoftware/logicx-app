import re
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


PRODUCT_FIELDS = (
	"name",
	"item",
	"item_source",
	"product_name",
	"short_description",
	"description",
	"enabled",
	"item_group",
	"collections",
	"ranking",
	"image",
	"has_variants",
	"price",
	"compare_at_price",
	"opening_stock",
	"highlights",
	"modified",
)

PRODUCT_WRITE_FIELDS = (
	"product_name",
	"short_description",
	"description",
	"enabled",
	"collections",
	"ranking",
	"image",
	"has_variants",
	"price",
	"compare_at_price",
	"opening_stock",
	"highlights",
)


class LogicXProduct(Document):
	def before_validate(self):
		item_details = frappe.db.get_value("Item", self.item, ["item_name", "item_group"], as_dict=True)
		if not item_details:
			frappe.throw(_("ERPNext Item {0} does not exist.").format(frappe.bold(self.item)))

		if not self.product_name:
			self.product_name = item_details.item_name or self.item
		self.item_group = item_details.item_group

	def validate(self):
		if flt(self.price) < 0 or flt(self.compare_at_price) < 0:
			frappe.throw(_("Product prices cannot be negative."))
		if flt(self.opening_stock) < 0:
			frappe.throw(_("Opening stock cannot be negative."))
		if cint(self.has_variants) and flt(self.opening_stock):
			frappe.throw(_("Opening stock cannot be set for a product with variants."))


@frappe.whitelist(methods=["POST"])
def create_new_product(product: dict[str, Any]) -> dict[str, Any]:
	frappe.has_permission("LogicX Product", ptype="create", throw=True)
	frappe.has_permission("Item", ptype="create", throw=True)

	values = _normalize_product(product)
	item = frappe.get_doc(_new_item_values(values)).insert()
	product_doc = frappe.get_doc(
		{
			"doctype": "LogicX Product",
			"item": item.name,
			"item_source": "Created by LogicX",
			**values,
		}
	).insert()
	return _serialize_product(product_doc)


@frappe.whitelist(methods=["POST"])
def link_existing_item(item: str, product: dict[str, Any]) -> dict[str, Any]:
	frappe.has_permission("LogicX Product", ptype="create", throw=True)
	frappe.has_permission("Item", ptype="read", doc=item, throw=True)

	item_details = frappe.db.get_value(
		"Item",
		item,
		["name", "item_name", "item_group", "description", "image", "has_variants", "standard_rate"],
		as_dict=True,
	)
	if not item_details:
		frappe.throw(_("ERPNext Item {0} does not exist.").format(frappe.bold(item)))

	values = _normalize_product(product, fallback_item=item_details)
	product_doc = frappe.get_doc(
		{
			"doctype": "LogicX Product",
			"item": item_details.name,
			"item_source": "Linked from ERPNext",
			**values,
		}
	).insert()
	return _serialize_product(product_doc)


def _normalize_product(product: dict[str, Any], fallback_item=None) -> dict[str, Any]:
	if not isinstance(product, dict):
		frappe.throw(_("Product details are required."))

	values = {field: product.get(field) for field in PRODUCT_WRITE_FIELDS}
	values["product_name"] = str(values.get("product_name") or "").strip()
	values["short_description"] = str(values.get("short_description") or "").strip()
	values["description"] = str(values.get("description") or "").strip()
	values["collections"] = str(values.get("collections") or "").strip()
	values["highlights"] = str(values.get("highlights") or "").strip()
	values["image"] = str(values.get("image") or "").strip() or None
	values["enabled"] = cint(values.get("enabled"))
	values["has_variants"] = cint(values.get("has_variants"))
	values["ranking"] = cint(values.get("ranking"))
	values["price"] = flt(values.get("price"))
	values["compare_at_price"] = flt(values.get("compare_at_price"))
	values["opening_stock"] = flt(values.get("opening_stock"))

	if fallback_item:
		values["product_name"] = values["product_name"] or fallback_item.item_name or fallback_item.name
		values["description"] = values["description"] or fallback_item.description or ""
		values["image"] = values["image"] or fallback_item.image
		values["has_variants"] = cint(product.get("has_variants", fallback_item.has_variants))
		values["price"] = flt(product.get("price", fallback_item.standard_rate))

	if not values["product_name"]:
		frappe.throw(_("Product name is required."))
	if values["price"] < 0 or values["compare_at_price"] < 0:
		frappe.throw(_("Product prices cannot be negative."))
	if values["opening_stock"] < 0:
		frappe.throw(_("Opening stock cannot be negative."))
	if values["has_variants"] and values["opening_stock"]:
		frappe.throw(_("Opening stock cannot be set for a product with variants."))

	return values


def _new_item_values(product: dict[str, Any]) -> dict[str, Any]:
	item_values = {
		"doctype": "Item",
		"item_code": _unique_item_code(product["product_name"]),
		"item_name": product["product_name"],
		"item_group": _stock_default("item_group", "Item Group", {"is_group": 0}),
		"stock_uom": _stock_default("stock_uom", "UOM"),
		"description": product["description"] or product["short_description"],
		"image": product["image"],
		"has_variants": product["has_variants"],
		"is_stock_item": 1,
		"is_sales_item": 1,
		"is_purchase_item": 1,
		"standard_rate": product["price"],
	}
	if product["opening_stock"]:
		item_values["opening_stock"] = product["opening_stock"]
		item_values["valuation_rate"] = product["price"]
	return item_values


def _stock_default(fieldname: str, doctype: str, filters: dict[str, Any] | None = None) -> str:
	value = frappe.db.get_single_value("Stock Settings", fieldname)
	if value and frappe.db.exists(doctype, value):
		return value

	values = frappe.get_all(doctype, filters=filters or {}, pluck="name", order_by="name asc", limit=1)
	if not values:
		frappe.throw(_("Configure a default {0} before creating products.").format(doctype))
	return values[0]


def _unique_item_code(product_name: str) -> str:
	base = re.sub(r"[^A-Za-z0-9]+", "-", product_name).strip("-").upper()[:120] or "ITEM"
	item_code = base
	sequence = 2
	while frappe.db.exists("Item", item_code):
		item_code = f"{base[:115]}-{sequence}"
		sequence += 1
	return item_code


def _serialize_product(product: Document) -> dict[str, Any]:
	return {field: product.get(field) for field in PRODUCT_FIELDS}
