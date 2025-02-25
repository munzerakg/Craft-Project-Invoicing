frappe.ui.form.on('Sales Order', {
	custom_order_invoicing_type: function (frm) {
		if (frm.doc.custom_order_invoicing_type && frm.doc.custom_order_invoicing_type == "Project Invoicing") {
			frm.set_value("enable_project_invoicing", 1);
		}
		else if (frm.doc.custom_order_invoicing_type && frm.doc.custom_order_invoicing_type == "Normal"){
			frm.set_value("enable_project_invoicing", 0);
		}
	},
	advance_percentage: function (frm) {
		let advance = frm.doc.advance_percentage ? parseFloat(frm.doc.advance_percentage) : 0;
		let retention = frm.doc.retention_percentage ? parseFloat(frm.doc.retention_percentage) : 0;
		
		frm.set_value("on_delivery_percentage", (advance || retention) ? (100 - (advance + retention)) : 0);
	},
	
	retention_percentage: function (frm) {
		let advance = frm.doc.advance_percentage ? parseFloat(frm.doc.advance_percentage) : 0;
		let retention = frm.doc.retention_percentage ? parseFloat(frm.doc.retention_percentage) : 0;
		
		frm.set_value("on_delivery_percentage", (advance || retention) ? (100 - (advance + retention)) : 0);
	},

	onload: function (frm) {
		if (frm.doc.enable_project_invoicing && frm.doc.retention_billed === 0) {
			frm.add_custom_button(__('Sales Invoice'), () => frm.events.make_sales_invoice(frm), __('Create'));
		}
	},

	make_sales_invoice: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
			frm: frm
		});
	},
	refresh: function(frm) {
        frm.add_custom_button("Proforma Invoice", function() {
            frappe.call({
                method: "craft_project_invoicing.events.sales_order.create_proforma_invoice",
                args: {
                    source_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.sync(r.message);
                        frappe.set_route("Form", r.message.doctype, r.message.name);
                    }
                }
            });
        }, "Create");
    }
});
