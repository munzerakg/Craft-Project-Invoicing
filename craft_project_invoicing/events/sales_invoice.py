import frappe
from frappe.utils import flt


def on_submit(doc, method):
	if doc.items and doc.sales_order:
		so_doc = frappe.get_doc("Sales Order", doc.sales_order)
		if so_doc.enable_project_invoicing:
			retention_account = frappe.db.get_value(
				"Item Default", {"parent": "Retention", "company": doc.company}, "income_account")
			adv_account = frappe.db.get_value(
				"Item Default", {"parent": "Advance", "company": doc.company}, "income_account")

			# Post reverse journal entry for advance invoice
			if doc.items and len(doc.items) == 1 and doc.items[0].item_code == "Advance":
				if not adv_account:
					frappe.throw(
						title="Advance Account Not Found",
						msg="Deafult income account not found in item <b>Advance</b>"
					)
				adv_amount = doc.items[0].get("amount")
				if not doc.items[0].get("income_account") == adv_account:
					ge_doc = frappe.get_doc({
						"doctype": "Journal Entry",
						"voucher_type": "Journal Entry",
						"company": doc.company,
						"posting_date": doc.posting_date,
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
					ge_doc.insert(ignore_permissions=True,
								  ignore_mandatory=True)
					ge_doc.submit()
					doc.db_set("ref_journal_entry", ge_doc.name)

				so_doc.db_set({
					"advance_billed": 1,
					"advance_ref_doc": doc.name,
					"advance_billed_amount": adv_amount,
					# "remaining_advance": adv_amount
				})

			# Post reverse journal entry for on Retention invoice
			elif doc.items and len(doc.items) == 1 and doc.items[0].item_code == "Retention":
				if not retention_account:
					frappe.throw(
						title="Retention Account Not Found",
						msg="Deafult income account not found in item <b>Retention</b>"
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
					ge_doc.insert(ignore_permissions=True,
								  ignore_mandatory=True)
					ge_doc.submit()
					doc.db_set("ref_journal_entry", ge_doc.name)

				so_doc.db_set({
					"retention_billed": 1,
					"retention_ref_doc": doc.name,
					"retention_billed_amount": ret_amount,
					# "remaining_retention": 0
				})

			# Post reverse journal entry for on multiple delivery invoices
			elif doc.items and len(doc.items) > 0:
				actual_delivery_amount = so_doc.base_net_total * \
					so_doc.on_delivery_percentage / 100
				so_doc.db_set("delivery_ref_doc", doc.name if not so_doc.delivery_ref_doc else (
					str(so_doc.delivery_ref_doc) + ", " + str(doc.name)))
				total = 0
				consumed_advance = 0
				# remaining_advance = 0
				consumed_retention = 0
				# remaining_retention = 0

				for t in doc.taxes:
					if t.is_advance and t.tax_amount:
						consumed_advance = so_doc.consumed_advance + \
							abs(t.tax_amount)
						# remaining_advance = so_doc.advance_billed_amount - (consumed_advance if consumed_advance else 0)
					elif t.is_retention and t.tax_amount:
						consumed_retention = so_doc.consumed_retention + \
							abs(t.tax_amount)
						# remaining_retention = (so_doc.base_net_total * (so_doc.retention_percentage/100)) - (consumed_retention if consumed_retention else 0)

					if t.is_advance or t.is_retention:
						total = total + t.tax_amount
				if actual_delivery_amount <= (float(so_doc.delivery_billed_amount if so_doc.delivery_billed_amount else 0) + doc.total + total):
					so_doc.db_set("on_delivery_billed", 1)
				so_doc.db_set({
					"delivery_billed_amount": so_doc.delivery_billed_amount + (doc.total + total),
					"consumed_advance": consumed_advance,
					"consumed_retention": consumed_retention,
					# "remaining_advance": remaining_advance,
					# "remaining_retention": remaining_retention
				})


# def validate(doc, method):
#     if doc.items and doc.sales_order:
#         for item in doc.items:
#             previous_data = frappe.db.sql("""
#                 SELECT SUM(sii.amount), SUM(sii.invoicing_percentage)
#                 FROM `tabSales Invoice Item` sii
#                 JOIN `tabSales Invoice` si ON sii.parent = si.name
#                 WHERE sii.item_code = %s 
#                 AND si.sales_order = %s 
#                 AND si.docstatus = 1
#                 AND si.name != %s
#             """, (item.item_code, doc.sales_order, doc.name))

#             previous_amount = previous_data[0][0] if previous_data and previous_data[0][0] else 0
#             previous_percentage = previous_data[0][1] if previous_data and previous_data[0][1] else 0

#             item.previous_amount = previous_amount
#             item.previous_percentage = previous_percentage
#             item.cumulative_amount = item.amount + previous_amount
#             item.cumulative_percentage = item.invoicing_percentage + previous_percentage



#     if doc.taxes and doc.sales_order:
#         for tax in doc.taxes:
#             condition = ""
#             params = [doc.sales_order, doc.name]

#             if tax.is_advance:
#                 condition = "AND stc.is_advance = 1"
#             elif tax.is_retention:
#                 condition = "AND stc.is_retention = 1"

#             previous_tax_amount = frappe.db.sql(f"""
#                 SELECT SUM(tax_amount) 
#                 FROM `tabSales Taxes and Charges` stc
#                 JOIN `tabSales Invoice` si ON stc.parent = si.name
#                 WHERE si.sales_order = %s 
#                 AND si.docstatus = 1
#                 AND si.name != %s
#                 {condition}
#             """, tuple(params))

#             tax.previous_amount = previous_tax_amount[0][0] if previous_tax_amount and previous_tax_amount[0][0] else 0
#             tax.cumulative_amount = tax.tax_amount + tax.previous_amount



def on_cancel(doc, method):
	invoice_type = {
		"Advance": "advance_billed",
		"Retention": "retention_billed"
	}
	invoice_references = {
		"Advance": "advance_ref_doc",
		"Retention": "retention_ref_doc"
	}
	billing_amounts = {
		"Advance": "advance_billed_amount",
		"Retention": "retention_billed_amount",
		"Delivery": "delivery_billed_amount"
	}
	if doc.ref_journal_entry:
		jv_doc_list = doc.ref_journal_entry.split(", ")
		for j in jv_doc_list:
			jv_doc = frappe.get_doc("Journal Entry", j)
			jv_doc.cancel()
	if doc.sales_order:
		so_doc = frappe.get_doc("Sales Order", doc.sales_order)
		if so_doc.enable_project_invoicing:
			delivery_ref_docs = None
			if doc.items and len(doc.items) == 1 and doc.items[0].item_code in ["Advance", "Retention"]:
				frappe.db.set_value("Sales Order", doc.sales_order, {
					invoice_type.get(doc.items[0].item_code): 0,
					invoice_references.get(doc.items[0].item_code): "",
					billing_amounts.get(doc.items[0].item_code): 0
				})
				if doc.items[0].item_code == "Retention":
					frappe.db.set_value("Sales Order", doc.sales_order, {
						"remaining_retention": float(so_doc.remaining_retention) - (doc.items[0].get("amount") if doc.items[0].get("amount") else 0)
					})
			elif doc.items and len(doc.items) > 0 and not doc.items[0].item_code in ["Advance", "Retention"]:
				frappe.db.set_value(
					"Sales Order", doc.sales_order, "on_delivery_billed", 0)
				delivery_ref_docs = frappe.db.get_value(
					"Sales Order", doc.sales_order, "delivery_ref_doc")

			if delivery_ref_docs:
				delivery_ref_doc_list = delivery_ref_docs.split(", ")
				delivery_ref_doc_list.remove(doc.name)
				frappe.db.set_value("Sales Order", doc.sales_order,
									"delivery_ref_doc", ", ".join(delivery_ref_doc_list))

				delivery_billed_amount = frappe.db.get_value(
					"Sales Order", doc.sales_order, "delivery_billed_amount")
				if delivery_billed_amount:
					total = 0
					consumed_advance = 0
					# remaining_advance = 0
					consumed_retention = 0
					# remaining_retention = 0
					for t in doc.taxes:
						if t.is_advance and t.tax_amount:
							consumed_advance = so_doc.consumed_advance - \
								abs(t.tax_amount)
							# remaining_advance = so_doc.advance_billed_amount - (consumed_advance if consumed_advance else 0)
						elif t.is_retention and t.tax_amount:
							consumed_retention = so_doc.consumed_retention - \
								abs(t.tax_amount)
							# remaining_retention = so_doc.retention_billed_amount - (consumed_retention if consumed_retention else 0)
						if t.is_advance or t.is_retention:
							total = total + t.tax_amount
					frappe.db.set_value("Sales Order", doc.sales_order, {
						billing_amounts.get("Delivery"): delivery_billed_amount - (doc.total + total),
						"consumed_advance": consumed_advance,
						"consumed_retention": consumed_retention,
						# "remaining_advance": remaining_advance,
						# "remaining_retention": remaining_retention
					})


import json

@frappe.whitelist()
def get_so_detail(sales_order, invoice_per=None, doc=None):
    if not sales_order:
        return None

    if doc:
        if isinstance(doc, str):
            doc = json.loads(doc)
        doc = frappe.get_doc(doc)

    invoice_per = flt(invoice_per) if invoice_per else None
    so_doc = frappe.get_doc("Sales Order", sales_order)

    if not so_doc.items:
        frappe.throw("Sales Order has no items or does not exist.")

    so_details = {}
    for item in so_doc.items:
        so_details[item.name] = {
            "so_detail": item.name,
            "so_qty": item.qty,
            "qty": item.qty
        }

    for item in doc.items:
        so_detail_key = item.get("so_detail")

        if so_detail_key and so_detail_key in so_details:
            invoice_percentage = flt(item.get("invoicing_percentage")) or invoice_per
            if invoice_percentage:
                so_details[so_detail_key]["qty"] = so_details[so_detail_key]["so_qty"] * (invoice_percentage / 100)

    return so_details if so_details else None


@frappe.whitelist()
def get_invoice_items(invoice_names, item_code, sales_order):
    invoice_names = frappe.parse_json(invoice_names)
    return frappe.get_all("Sales Invoice Item", 
                          filters={"parent": ["in", invoice_names], "item_code": item_code, "sales_order": sales_order},
                          fields=["amount", "invoicing_percentage","advance_amount","balance_amount_ad","retention_amount","balance_amount_ret"])
