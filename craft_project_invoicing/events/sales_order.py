import frappe

def validate(doc, method):
    if doc.enable_project_invoicing and (doc.advance_percentage or doc.on_delivery_percentage or doc.retention_percentage):
        try:
            total = float(doc.advance_percentage or 0) + \
                    float(doc.on_delivery_percentage or 0) + \
                    float(doc.retention_percentage or 0)
                    
            if total != 100:
                frappe.throw(
                    title='Error',
                    msg='Total of Advance, On Delivery and Retention should be <b>100%</b>'
                )
        except ValueError:
            frappe.throw(
                title='Error',
                msg='Advance, On Delivery, and Retention percentages must be numeric values.'
            )



from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def create_proforma_invoice(source_name, target_doc=None):
    doc = get_mapped_doc(
        "Sales Order",                     
        source_name,                       
        {
            "Sales Order": {               
                "doctype": "Proforma Invoice",  
                "field_map": {                  
                    "name": "against_sales_order",      
                    "customer": "customer",     
                    "transaction_date": "transaction_date",
                    "delivery_date" : "delivery_date"
                }
            },
            "Sales Order Item": {           
                "doctype": "Proforma Invoice Item",
                "field_map": {               
                    "item_code": "item_code",
                    "qty": "qty",
                    "rate": "rate",
                    "amount": "amount",
                    "description": "description",
                    "name": "so_item_detail",
                    "delivery_date" : "delivery_date"
                    
                }
            }
        },
        target_doc                           
    )
    return doc
