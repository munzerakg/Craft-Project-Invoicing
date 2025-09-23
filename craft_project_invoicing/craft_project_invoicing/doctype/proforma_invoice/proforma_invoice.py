# Copyright (c) 2025, Craftint and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.utils import get_fetch_values
from erpnext.accounts.party import get_party_account
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, getdate, nowdate, strip_html
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from frappe.model.mapper import get_mapped_doc

class ProformaInvoice(Document):
    def validate(self):
        if not self.delivery_date:
            return

        for item in self.items:
            if not item.delivery_date:
                item.delivery_date = self.delivery_date
  
        sales_order = frappe.get_doc("Sales Order", self.sales_order)

        so_total = sales_order.total  
        pi_total = self.total 

        if pi_total > so_total:
            frappe.throw(f"The total amount in Proforma Invoice ({pi_total}) cannot exceed the Sales Order total ({so_total}).")
        
        if self.items and self.sales_order:
            for item in self.items:
                previous_data = frappe.db.sql("""
                    SELECT SUM(pii.amount), SUM(pii.invoicing_percentage)
                    FROM `tabProforma Invoice Item` pii
                    JOIN `tabProforma Invoice` pi ON pii.parent = pi.name
                    WHERE pii.item_code = %s 
                    AND pi.sales_order = %s 
                    AND pi.docstatus = 1
                    AND pi.name != %s
                """, (item.item_code, self.sales_order, self.name))

                previous_amount = previous_data[0][0] if previous_data and previous_data[0][0] else 0
                previous_percentage = previous_data[0][1] if previous_data and previous_data[0][1] else 0

                item.previous_amount = previous_amount
                item.previous_percentage = previous_percentage
                item.cumulative_amount = flt(item.amount) + flt(previous_amount)
                item.cumulative_percentage = flt(item.invoicing_percentage) + flt(previous_percentage)


        if self.taxes and self.sales_order:
            for tax in self.taxes:
                condition = ""
                params = [self.sales_order, self.name]

                if tax.is_advance:
                    condition = "AND stc.is_advance = 1"
                elif tax.is_retention:
                    condition = "AND stc.is_retention = 1"

                previous_tax_amount = frappe.db.sql(f"""
                    SELECT SUM(tax_amount) 
                    FROM `tabSales Taxes and Charges` stc
                    JOIN `tabSales Invoice` si ON stc.parent = si.name
                    WHERE si.sales_order = %s 
                    AND si.docstatus = 1
                    AND si.name != %s
                    {condition}
                """, tuple(params))

                tax.previous_amount = previous_tax_amount[0][0] if previous_tax_amount and previous_tax_amount[0][0] else 0
                tax.cumulative_amount = tax.tax_amount + tax.previous_amount




@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
	def postprocess(source, target):
		set_missing_values(source, target)
		# Get the advance paid Journal Entries in Sales Invoice Advance
		if target.get("allocate_advances_automatically"):
			target.set_advances()

	def set_missing_values(source, target):
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")
		target.run_method("set_use_serial_batch_fields")

		if source.company_address:
			target.update({"company_address": source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", "company_address", target.company_address))

		# set the redeem loyalty points if provided via shopping cart
		if source.loyalty_points and source.order_type == "Shopping Cart":
			target.redeem_loyalty_points = 1

		target.debit_to = get_party_account("Customer", source.customer, source.company)

	def update_item(source, target, source_parent):
		target.amount = flt(source.amount) - flt(source.billed_amt)
		target.base_amount = target.amount * flt(source_parent.conversion_rate)
		target.qty = (
			target.amount / flt(source.rate)
			if (source.rate and source.billed_amt)
			else source.qty - source.returned_qty
		)

		if source_parent.project:
			target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center")
		if target.item_code:
			item = get_item_defaults(target.item_code, source_parent.company)
			item_group = get_item_group_defaults(target.item_code, source_parent.company)
			cost_center = item.get("selling_cost_center") or item_group.get("selling_cost_center")

			if cost_center:
				target.cost_center = cost_center

	doclist = get_mapped_doc(
		"Proforma Invoice",
		source_name,
		{
			"Proforma Invoice": {
				"doctype": "Sales Invoice",
				"field_map": {
					"party_account_currency": "party_account_currency",
					"payment_terms_template": "payment_terms_template",
                    "sales_order":"sale_order",
                    "name": "custom_proforma__invoice_ref",
                    "custom_invoice_percentage" : "custom_invoice_percentage",
				},
				"field_no_map": ["payment_terms_template"],
				"validation": {"docstatus": ["=", 1]},
			},
			"Proforma Invoice Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {
					"so_item_detail": "so_detail",
					"sales_order": "sales_order",
                    "parent": "custom_proforma_invoice",
                    "name": "custom_proforma_invoice_item"
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.qty
				and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
		},
		target_doc,
		postprocess,
		ignore_permissions=ignore_permissions,
	)

	automatically_fetch_payment_terms = cint(
		frappe.db.get_single_value("Accounts Settings", "automatically_fetch_payment_terms")
	)
	if automatically_fetch_payment_terms:
		doclist.set_payment_schedule()

	return doclist



from frappe.utils import flt


def on_submit(doc, method):
    if doc.items and doc.sales_order:
        so_doc = frappe.get_doc("Sales Order", doc.sales_order)
        if so_doc.enable_project_invoicing:
            retention_account = frappe.db.get_value(
                "Item Default", {"parent": "Retention", "company": doc.company}, "income_account")
            adv_account = frappe.db.get_value(
                "Item Default", {"parent": "Advance", "company": doc.company}, "income_account")

            # Handle reverse journal entry for advance invoice
            if doc.items and len(doc.items) == 1 and doc.items[0].item_name == "Advance":
                if not adv_account:
                    frappe.throw(
                        title="Advance Account Not Found",
                        msg="Default income account not found in item <b>Advance</b>"
                    )
                adv_amount = doc.items[0].get("amount")
                if not doc.items[0].get("income_account") == adv_account:
                    ge_doc = frappe.get_doc({
                        "doctype": "Journal Entry",
                        "voucher_type": "Journal Entry",
                        "company": doc.company,
                        "posting_date": doc.transaction_date,
                        "sales_order_reference": doc.sales_order
                    })
                    ge_doc.append("accounts", {
                        "account": doc.items[0].get("income_account"),
                        "debit_in_account_currency": adv_amount,
                        "credit_in_account_currency": 0,
                        "project": doc.project,
                        "cost_center": doc.items[0].get("cost_center")
                    })
                    ge_doc.append("accounts", {
                        "account": adv_account,
                        "debit_in_account_currency": 0,
                        "credit_in_account_currency": adv_amount,
                        "project": doc.project,
                        "cost_center": doc.items[0].get("cost_center")
                    })
                    ge_doc.insert(ignore_permissions=True, ignore_mandatory=True)
                    ge_doc.submit()
                    doc.db_set("ref_journal_entry", ge_doc.name)

                so_doc.db_set({
                    "advance_billed": 1,
                    "advance_ref_doc": doc.name,
                    "advance_billed_amount": adv_amount,
                })

            # Handle reverse journal entry for retention invoice
            elif doc.items and len(doc.items) == 1 and doc.items[0].item_name == "Retention":
                if not retention_account:
                    frappe.throw(
                        title="Retention Account Not Found",
                        msg="Default income account not found in item <b>Retention</b>"
                    )
                ret_amount = doc.items[0].get("amount")
                if not doc.items[0].get("income_account") == retention_account:
                    ge_doc = frappe.get_doc({
                        "doctype": "Journal Entry",
                        "voucher_type": "Journal Entry",
                        "company": doc.company,
                        "posting_date": doc.posting_date,
                        "sales_order_reference": doc.sales_order
                    })
                    ge_doc.append("accounts", {
                        "account": doc.items[0].get("income_account"),
                        "debit_in_account_currency": ret_amount,
                        "credit_in_account_currency": 0,
                        "project": doc.project,
                        "cost_center": doc.items[0].get("cost_center")
                    })
                    ge_doc.append("accounts", {
                        "account": retention_account,
                        "debit_in_account_currency": 0,
                        "credit_in_account_currency": ret_amount,
                        "project": doc.project,
                        "cost_center": doc.items[0].get("cost_center")
                    })
                    ge_doc.insert(ignore_permissions=True, ignore_mandatory=True)
                    ge_doc.submit()
                    doc.db_set("ref_journal_entry", ge_doc.name)

                so_doc.db_set({
                    "retention_billed": 1,
                    "retention_ref_doc": doc.name,
                    "retention_billed_amount": ret_amount,
                })

            # Handle reverse journal entry for multiple delivery invoices
            elif doc.items and len(doc.items) > 0:
                actual_delivery_amount = so_doc.base_net_total * so_doc.on_delivery_percentage / 100
                so_doc.db_set("delivery_ref_doc", doc.name if not so_doc.delivery_ref_doc else (
                    str(so_doc.delivery_ref_doc) + ", " + str(doc.name)))
                total = 0
                consumed_advance = 0
                consumed_retention = 0

                for t in doc.taxes:
                    if t.is_advance and t.tax_amount:
                        consumed_advance = so_doc.consumed_advance + abs(t.tax_amount)
                    elif t.is_retention and t.tax_amount:
                        consumed_retention = so_doc.consumed_retention + abs(t.tax_amount)
                    if t.is_advance or t.is_retention:
                        total = total + t.tax_amount

                if actual_delivery_amount <= (float(so_doc.delivery_billed_amount if so_doc.delivery_billed_amount else 0) + doc.total + total):
                    so_doc.db_set("on_delivery_billed", 1)

                so_doc.db_set({
                    "delivery_billed_amount": so_doc.delivery_billed_amount + (doc.total + total),
                    "consumed_advance": consumed_advance,
                    "consumed_retention": consumed_retention,
                })


# def on_cancel(doc, method):
#     invoice_type = {
#         "Advance": "advance_billed",
#         "Retention": "retention_billed"
#     }
#     invoice_references = {
#         "Advance": "advance_ref_doc",
#         "Retention": "retention_ref_doc"
#     }
#     billing_amounts = {
#         "Advance": "advance_billed_amount",
#         "Retention": "retention_billed_amount",
#         "Delivery": "delivery_billed_amount"
#     }
#     if doc.ref_journal_entry:
#         jv_doc_list = doc.ref_journal_entry.split(", ")
#         for j in jv_doc_list:
#             jv_doc = frappe.get_doc("Journal Entry", j)
#             jv_doc.cancel()
#     if doc.sales_order:
#         so_doc = frappe.get_doc("Sales Order", doc.sales_order)
#         if so_doc.enable_project_invoicing:
#             delivery_ref_docs = None
#             if doc.items and len(doc.items) == 1 and doc.items[0].item_code in ["Advance", "Retention"]:
#                 frappe.db.set_value("Sales Order", doc.sales_order, {
#                     invoice_type.get(doc.items[0].item_code): 0,
#                     invoice_references.get(doc.items[0].item_code): "",
#                     billing_amounts.get(doc.items[0].item_code): 0
#                 })
#                 if doc.items[0].item_code == "Retention":
#                     frappe.db.set_value("Sales Order", doc.sales_order, {
#                         "remaining_retention": float(so_doc.remaining_retention) - (doc.items[0].get("amount") if doc.items[0].get("amount") else 0)
#                     })
#             elif doc.items and len(doc.items) > 0 and not doc.items[0].item_code in ["Advance", "Retention"]:
#                 frappe.db.set_value("Sales Order", doc.sales_order, "on_delivery_billed", 0)
#                 delivery_ref_docs = frappe.db.get_value(
#                     "Sales Order", doc.sales_order, "delivery_ref_doc")

#             if delivery_ref_docs:
#                 delivery_ref_doc_list = delivery_ref_docs.split(", ")
#                 delivery_ref_doc_list.remove(doc.name)
#                 frappe.db.set_value("Sales Order", doc.sales_order,
#                                     "delivery_ref_doc", ", ".join(delivery_ref_doc_list))

#                 delivery_billed_amount = frappe.db.get_value(
#                     "Sales Order", doc.sales_order, "delivery_billed_amount")
#                 if delivery_billed_amount:
#                     total = 0
#                     consumed_advance = 0
#                     consumed_retention = 0
#                     for t in doc.taxes:
#                         if t.is_advance and t.tax_amount:
#                             consumed_advance = so_doc.consumed_advance - abs(t.tax_amount)
#                         elif t.is_retention and t.tax_amount:
#                             consumed_retention = so_doc.consumed_retention - abs(t.tax_amount)
#                         if t.is_advance or t.is_retention:
#                             total = total + t.tax_amount
#                     frappe.db.set_value("Sales Order", doc.sales_order, {
#                         billing_amounts.get("Delivery"): delivery_billed_amount - (doc.total + total),
#                         "consumed_advance": consumed_advance,
#                         "consumed_retention": consumed_retention,
#                     })


@frappe.whitelist()
def get_so_item_detail(sales_order, invoice_per=None, doc=None):
	import json
	if not sales_order:
		return

	if doc:
		if isinstance(doc, str):
			doc = json.loads(doc)
			doc = frappe.get_doc(doc)
		
		if invoice_per and isinstance(invoice_per, str):
			invoice_per = flt(invoice_per)

		so_doc = frappe.get_doc("Sales Order", sales_order)
		so_item_details = {}
		if so_doc and so_doc.items:
			for item in so_doc.items:
				detail_dict = frappe._dict({
					"so_item_detail": item.name,
					"so_qty": item.qty,
					"qty": item.qty * (invoice_per/100) if invoice_per else item.qty
				})
				so_item_details[item.name] = detail_dict
		for i in doc.items:
			if i.invoicing_percentage and i.so_item_detail:
				detail = so_item_details[i.so_item_detail]
				detail["qty"] = detail["so_qty"] * (i.invoicing_percentage / 100)

		return so_item_details if so_item_details else None




@frappe.whitelist()
def validate_invoice_percentage_total(
    sales_order,
    current_invoice=None,            
    custom_invoice_percentage=0,
    items=None,
):
    """
    Validate that:
    1) The overall (header) invoicing percentage across all submitted Sales Invoices
       + the current Proforma's header percentage does not exceed 100.
    2) No individual Sales Order Item crosses 100% when adding the current Proforma's
       item-level invoicing_percentage to what has already been invoiced in submitted
       Sales Invoices.

    NOTE: This function intentionally checks ONLY against submitted Sales Invoices.
    If you also want to include other Proformas, add another aggregation the same way.
    """
    import json
    from frappe.utils import flt

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []
    items = items or []

    prev_invoice_names = frappe.get_all(
        "Sales Invoice",
        filters={
            "sales_order": sales_order,
            "docstatus": 1,
            "name": ["!=", current_invoice],
        },
        pluck="name",
    )

    total_percentage = sum([
        flt(frappe.db.get_value("Sales Invoice", inv, "custom_invoice_percentage"))
        for inv in prev_invoice_names
    ])
    total_percentage += flt(custom_invoice_percentage)

    prev_item_rows = frappe.db.sql(
        """
        SELECT
            sii.so_detail,
            sii.item_code,
            SUM(COALESCE(sii.invoicing_percentage, 0)) AS total_perc
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE
            si.sales_order = %s
            AND si.docstatus = 1
            AND si.name != %s
        GROUP BY sii.so_detail, sii.item_code
        """,
        (sales_order, current_invoice or ""),
        as_dict=True,
    )

    prev_item_totals = {
        (r.so_detail or r.item_code): flt(r.total_perc) for r in prev_item_rows
    }

    items_exceeding = []
    for idx, it in enumerate(items, start=1):
        key = it.get("so_detail") or it.get("sales_order_item") or it.get("item_code")
        current_item_perc = flt(it.get("invoicing_percentage", custom_invoice_percentage))
        prev_item_perc = flt(prev_item_totals.get(key, 0))
        total_item_perc = prev_item_perc + current_item_perc

        if total_item_perc > 100:
            items_exceeding.append({
                "row_idx": idx,               
                "so_detail": key,
                "item_code": it.get("item_code"),
                "prev": prev_item_perc,
                "current": current_item_perc,
                "total": total_item_perc,
            })

    return {
        "total_invoice_percent": total_percentage,
        "items_exceeding": items_exceeding,
    }


@frappe.whitelist()
def get_remaining_qty_from_so(sales_order, current_invoice=None):
    from collections import defaultdict
    import frappe

    so_items = frappe.db.get_all("Sales Order Item",
        filters={"parent": sales_order},
        fields=["item_code", "rate", "qty"]
    )

    so_item_map = {}
    for i in so_items:
        key = f"{i.item_code}||{flt(i.rate)}"
        so_item_map[key] = flt(i.qty)

    pi_items = frappe.db.sql("""
        SELECT pii.item_code, pii.rate, pii.qty
        FROM `tabProforma Invoice` pi
        JOIN `tabProforma Invoice Item` pii ON pii.parent = pi.name
        WHERE pi.sales_order = %s AND pi.docstatus = 1
        {exclude_clause}
    """.format(exclude_clause="AND pi.name != %s" if current_invoice else ""),
        (sales_order, current_invoice) if current_invoice else (sales_order,),
        as_dict=True
    )

    invoiced_qty_map = defaultdict(float)
    for row in pi_items:
        key = f"{row.item_code}||{flt(row.rate)}"
        invoiced_qty_map[key] += flt(row.qty)

    remaining_qty_map = {}
    for key, so_qty in so_item_map.items():
        remaining_qty = so_qty - invoiced_qty_map.get(key, 0)
        remaining_qty_map[key] = max(remaining_qty, 0)
    
    print(remaining_qty_map,11111111111)

    return remaining_qty_map
