frappe.ui.form.on('Sales Invoice', {
    // custom_invoice_percentage:function(frm){
    //     if (frm.doc.custom_invoice_percentage > 100) {
    //         frappe.throw(__("Invoice percentage cannot be greater than 100"));
    //     }

    //     if (frm.doc.sales_order && frm.doc.custom_invoice_percentage) {
    //         frappe.call({
    //             method: "frappe.get_list",
    //             args: {
    //                 doctype: "Sales Invoice",
    //                 filters: {
    //                     sales_order: frm.doc.sales_order,
    //                     docstatus: 1,
    //                     name: ["!=", frm.doc.name]  // Exclude current invoice
    //                 },
    //                 fields: ["name"]
    //             },
    //             callback: function (r) {
    //                 if (r.message && r.message.length > 0) {
    //                     let invoice_names = r.message.map(d => d.name);

    //                     frappe.call({
    //                         method: "craft_project_invoicing.events.sales_invoice.get_invoice_percentage_sum",
    //                         args: {
    //                             invoice_names: invoice_names
    //                         },
    //                         callback: function (res) {
    //                             let previous_total = flt(res.message || 0);
    //                             let new_total = previous_total + flt(frm.doc.custom_invoice_percentage);
    //                             if (new_total > 100) {
    //                                 frappe.throw(__("Total invoice percentage exceeds 100%. Currently: {0}%", [new_total]));
    //                             }
    //                         }
    //                     });
    //                 }
    //             }
    //         });
    //     }
    // },
	onload_post_render: function (frm) {
		if (frm.doc.sales_order && frm.doc.__islocal) {
			frappe.db.get_doc("Sales Order", frm.doc.sales_order)
				.then(doc => {
					if (doc.enable_project_invoicing) {
						let adv_amount = doc.base_net_total * (doc.advance_percentage / 100);
						let delivery_amount = doc.base_net_total * (doc.on_delivery_percentage / 100);
						let balance_delivery_amount = 0;
						if (doc.advance_billed && !doc.retention_billed) {
							balance_delivery_amount = delivery_amount - (doc.total_billed_amount - adv_amount);
						}
						let retention = doc.base_net_total * (doc.retention_percentage / 100);

						// Advance Billing
						if (!doc.advance_billed && doc.advance_percentage && doc.base_net_total) {
							frappe.db.get_value("Item", { item_name: "Advance" }, "name")
								.then(res => {
									if (!res.message || !res.message.name) {
										frappe.throw(__("Item with item name 'Advance' not found."));
									}
									return frappe.db.get_doc("Item", res.message.name);
								})
								.then(item_doc => {
									let income_account = '';
									$.each(item_doc.item_defaults, function (k, i) {
										if (i.company == frm.doc.company) {
											income_account = i.income_account;
										}
									});
									let rate = adv_amount;
									frm.clear_table("items");
									let row = frm.add_child("items", {
										item_code: item_doc.name,
										item_name: item_doc.item_name,
										rate: rate,
										qty: 1,
										conversion_factor: 1,
										uom: item_doc.stock_uom,
										description: item_doc.description,
										sales_order: doc.sales_order,
										income_account: income_account,
										project: frm.doc.project,
										cost_center: frm.doc.cost_center
									});
									frm.trigger('rate', row.doctype, row.name);
									frm.refresh_fields("items");
								});
							set_taxes(frm, frm.doc.sales_order);
						}
						// Retention Billing
						else if (doc.advance_billed && doc.on_delivery_billed && !doc.retention_billed && doc.retention_percentage && doc.base_net_total) {
							frappe.db.get_value("Item", { item_name: "Retention" }, "name")
								.then(res => {
									if (!res.message || !res.message.name) {
										frappe.throw(__("Item with item name 'Retention' not found."));
									}
									return frappe.db.get_doc("Item", res.message.name);
								})
								.then(item_doc => {
									let income_account = '';
									$.each(item_doc.item_defaults, function (k, i) {
										if (i.company == frm.doc.company) {
											income_account = i.income_account;
										}
									});
									let rate = doc.base_net_total * (doc.retention_percentage / 100);
									frm.clear_table("items");
									let row = frm.add_child("items", {
										item_code: item_doc.name,
										item_name: item_doc.item_name,
										rate: rate,
										qty: 1,
										conversion_factor: 1,
										uom: item_doc.stock_uom,
										description: item_doc.description,
										sales_order: doc.sales_order,
										income_account: income_account,
										project: frm.doc.project,
										cost_center: frm.doc.cost_center
									});
									frm.trigger('rate', row.doctype, row.name);
									frm.refresh_fields("items");
									if (!frm.doc.taxes_and_charges) {
										set_taxes(frm, frm.doc.sales_order);
									}
								});
						} else {
							frappe.db.get_value("Company", frm.doc.company, "project_invoicing_tax_template")
								.then(r => {
									if (r.message) {
										frm.set_value("taxes_and_charges", r.message.project_invoicing_tax_template);
										setTimeout(() => {
											$.each(frm.doc.taxes, function (k, t) {
												if (t.is_advance && !t.is_retention) {
													frappe.model.set_value(t.doctype, t.name, "rate", -(doc.advance_percentage));
												} else if (!t.is_advance && t.is_retention) {
													frappe.model.set_value(t.doctype, t.name, "rate", -(doc.retention_percentage));
												}
											});
										}, 1000);
									}
									else {
										frappe.throw({ message: __("Project invoicing template not found in company"), title: __("Message") })
									}
								});
						}
					}
				});
		}
	},

	// validate: function (frm) {
    //     if (frm.doc.items && frm.doc.items.length > 0) {
    //         let promises = [];
    
    //         $.each(frm.doc.items, function (index, row) {
    //             if (!row.sales_order) return;
    
    //             let p = new Promise(resolve => {
    //                 frappe.call({
    //                     method: "craft_project_invoicing.events.sales_invoice.get_so_detail",
    //                     args: {
    //                         "sales_order": row.sales_order,
    //                         "invoice_per": frm.doc.custom_invoice_percentage,
    //                         "doc": frm.doc
    //                     },
    //                     callback: function (r) {
    //                         if (r.message) {
    //                             if (r.message[row.so_detail]) {
    //                                 frappe.model.set_value(row.doctype, row.name, "custom_so_qty", r.message[row.so_detail].so_qty);
    //                                 if (r.message[row.so_detail].qty) {
    //                                     frappe.model.set_value(row.doctype, row.name, "qty", r.message[row.so_detail].qty);
    //                                 }
    //                             }
    //                             if (frm.doc.custom_invoice_percentage && !row.invoicing_percentage) {
    //                                 frappe.model.set_value(row.doctype, row.name, "invoicing_percentage", frm.doc.custom_invoice_percentage);
    //                             }
    //                         }
    //                         frappe.call({
    //                             method: "frappe.client.get_value",
    //                             args: {
    //                                 doctype: "Sales Order",
    //                                 filters: { name: row.sales_order },
    //                                 fieldname: ["advance_percentage", "retention_percentage"]
    //                             },
    //                             callback: function (r2) {
    //                                 if (r2.message) {
    //                                     let advance_percent = r2.message.advance_percentage || 0;
    //                                     let retention_percent = r2.message.retention_percentage || 0;
    //                                     let qty = row.qty || 0;
    //                                     let rate = row.rate || 0;
    //                                     let calculated_amount = qty * rate;
    
    //                                     frappe.model.set_value(row.doctype, row.name, "advance_percent", advance_percent);
    //                                     frappe.model.set_value(row.doctype, row.name, "retention_percent", retention_percent);
    
    //                                     let advance_amount = (calculated_amount * advance_percent) / 100;
    //                                     frappe.model.set_value(row.doctype, row.name, "advance_amount", advance_amount);
    //                                 }
    //                                 resolve();
    //                             }
    //                         });
    //                     }
    //                 });
    //             });
    //             promises.push(p);
    //         });
    
    //         Promise.all(promises).then(() => {
    //             frm.refresh_field("items");
    //         });
    //     }
    // }

    validate: async function (frm) {
        if (!frm.doc.items || frm.doc.items.length === 0) return;

        if (frm.doc.custom_invoice_percentage && frm.doc.custom_invoice_percentage > 100) {
            frappe.throw(__("Invoice percentage cannot be greater than 100"));
        }

        frm.doc.items.forEach(row => {
            if (row.invoicing_percentage && row.invoicing_percentage > 100) {
                frappe.throw(__("Row #{0}: Invoicing Percentage cannot be greater than 100%", [row.idx]));
            }
        });

        
        if (frm.doc.sales_order && frm.doc.custom_invoice_percentage) {
            const items_payload = (frm.doc.items || []).map(d => ({
                so_detail: d.so_detail || d.sales_order_item,
                item_code: d.item_code,
                invoicing_percentage: flt(d.invoicing_percentage || frm.doc.custom_invoice_percentage)
            }));

            const res = await frappe.call({
                method: "craft_project_invoicing.events.sales_invoice.validate_invoice_percentage_total",
                args: {
                    sales_order: frm.doc.sales_order,
                    current_invoice: frm.doc.name,
                    custom_invoice_percentage: frm.doc.custom_invoice_percentage,
                    items: items_payload
                }
            });

            const out = res.message || {};
            const total_invoice_percent = flt(out.total_invoice_percent);

            if (total_invoice_percent > 100) {
                frappe.throw(__("Total invoice percentage exceeds 100%. Currently: {0}%", [total_invoice_percent]));
            }

            if (out.items_exceeding && out.items_exceeding.length > 0) {
                const lines = out.items_exceeding.map((d, idx) =>
                    `Row #${idx + 1}: Invoicing percentage exceeds 100%.<br>` +
                    `Total : <b>${d.total}%</b> (Current: ${d.current}%, Previous: ${d.prev}%)`
                );
                frappe.throw(lines.join("<br><br>"));
            }



        }

        let promises = frm.doc.items.map(async (row) => {
            if (row.sales_order) {
                let so_detail_resp = await frappe.call({
                    method: "craft_project_invoicing.events.sales_invoice.get_so_detail",
                    args: {
                        sales_order: row.sales_order,
                        invoice_per: frm.doc.custom_invoice_percentage,
                        doc: frm.doc
                    }
                });
    
                if (so_detail_resp.message && so_detail_resp.message[row.so_detail]) {
                    frappe.model.set_value(row.doctype, row.name, "custom_so_qty", so_detail_resp.message[row.so_detail].so_qty);
                    if (so_detail_resp.message[row.so_detail].qty) {
                        frappe.model.set_value(row.doctype, row.name, "qty", so_detail_resp.message[row.so_detail].qty);
                    }
                }
    
                if (frm.doc.custom_invoice_percentage && !row.invoicing_percentage) {
                    frappe.model.set_value(row.doctype, row.name, "invoicing_percentage", frm.doc.custom_invoice_percentage);
                }
    
                let get_value_resp = await frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Sales Order",
                        filters: { name: row.sales_order },
                        fieldname: ["advance_percentage", "retention_percentage"]
                    }
                });
    
                if (get_value_resp.message) {
                    let advance_percent = get_value_resp.message.advance_percentage || 0;
                    let retention_percent = get_value_resp.message.retention_percentage || 0;
                    let calculated_amount = (row.qty || 0) * (row.rate || 0);
    
                    frappe.model.set_value(row.doctype, row.name, "advance_percent", advance_percent);
                    frappe.model.set_value(row.doctype, row.name, "retention_percent", retention_percent);
    
                    frappe.model.set_value(row.doctype, row.name, "advance_amount", (calculated_amount * advance_percent) / 100);
                    frappe.model.set_value(row.doctype, row.name, "retention_amount", (calculated_amount * retention_percent) / 100);
                }
            }
        });
    
        await Promise.all(promises);
    
        let total_advance_amount = frm.doc.items.reduce((sum, row) => {
            let calculated_amount = (row.qty || 0) * (row.rate || 0);
            let advance_amount = (calculated_amount * (row.advance_percent || 0)) / 100;
            return sum + advance_amount;
        }, 0);
    
        let total_retention_amount = frm.doc.items.reduce((sum, row) => {
            let calculated_amount = (row.qty || 0) * (row.rate || 0);
            let retention_amount = (calculated_amount * (row.retention_percent || 0)) / 100;
            return sum + retention_amount;
        }, 0);
    
        if (frm.doc.taxes && frm.doc.taxes.length > 0) {
            frm.doc.taxes.forEach(tax => {
                if (tax.is_advance == 1) {
                    frappe.model.set_value(tax.doctype, tax.name, "tax_amount", -total_advance_amount);
                }
                if (tax.is_retention == 1) {
                    frappe.model.set_value(tax.doctype, tax.name, "tax_amount", -total_retention_amount);
                }
            });
            frm.refresh_field("taxes");
        }
    
        frm.refresh_field("items");
    }
});

var set_taxes = function(frm, sales_order) {
	frappe.db.get_value("Sales Order", sales_order, "taxes_and_charges")
	.then(r => {
		if (r.message.taxes_and_charges) {
			setTimeout(() => {
				frm.set_value("taxes_and_charges", r.message.taxes_and_charges);
				frm.trigger("taxes_and_charges", frm.doc.doctype, frm.doc.name);
			}, 1000);
		}
	})
};