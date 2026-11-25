frappe.ui.form.on("KRA eTIMS Settings", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Initialize VSCU Device"), () => {
                frappe.call({
                    method: "kra_etims.etims.initialize_device",
                    freeze: true,
                    freeze_message: __("Initializing VSCU device..."),
                    callback(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __("VSCU Initialization"),
                                indicator: r.message.resultCd === "000" ? "green" : "red",
                                message: `<pre>${JSON.stringify(r.message, null, 2)}</pre>`,
                            });
                        }
                    },
                });
            }, __("Actions"));

            frm.add_custom_button(__("Test Connection (Sync Codes)"), () => {
                frappe.call({
                    method: "kra_etims.etims.test_connection",
                    freeze: true,
                    freeze_message: __("Testing VSCU connection..."),
                    callback(r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: __("VSCU Connection Test"),
                                indicator: r.message.resultCd === "000" ? "green" : "red",
                                message: `Result: <b>${r.message.resultCd}</b> — ${r.message.resultMsg || ""}`,
                            });
                        }
                    },
                });
            }, __("Actions"));
        }
    },
});
