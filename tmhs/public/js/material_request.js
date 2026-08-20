frappe.ui.form.on("Material Request", {
    refresh: function (frm) {
        frm.add_custom_button(
            __("Create Vendor Bill"),
            () => frm.events.create_vendor_bill(frm),
            __("Create")
        )
    },
    create_vendor_bill: function (frm) {
        let vendor_bill = frappe.model.get_new_doc("Purchase Invoice");

        // Copy fields from current document
        //vendor_bill.title = frm.doc.title;
        vendor_bill.supplier = frm.doc.supplier;
        //vendor_bill.material_request_type = frm.doc.material_request_type;
        //vendor_bill.department = frm.doc.department;
        vendor_bill.cost_center = frm.doc.cost_center;
        vendor_bill.transaction_date = frm.doc.posting_date;
        //vendor_bill.from = frm.doc.from;
        //vendor_bill.schedule_date = frm.doc.schedule_date
        //vendor_bill.set_warehouse = frm.doc.set_warehouse

        frm.doc.items.forEach(function (item) {

            let new_item = frappe.model.add_child(
                vendor_bill,
                "Purchase Invoice Item",
                "items"
            );

            //new_item.item_code = item.item_code;
            new_item.description = item.description;
            //new_item.qty = item.qty;
            new_item.uom = item.uom;
            //new_item.actual_qty = item.actual_qty;
            //new_item.other_stores = item.other_stores
            new_item.rate = item.rate
            new_item.amount = item.amount;
            new_item.item_code = item.item_code
            new_item.item_name = item.item_name
            new_item.qty = item.qty
        });

        frappe.set_route(
            "Form",
            "Purchase Invoice",
            vendor_bill.name
        );
    },
})