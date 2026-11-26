app_name = "kra_etims"
app_title = "KRA eTIMS"
app_publisher = "houssen10"
app_description = "KRA eTIMS VSCU integration for ERPNext using vscu-python-sdk"
app_email = "admin@example.com"
app_license = "MIT"

add_to_apps_screen = [
    {
        "name": app_name,
        "logo": "/assets/kra_etims/images/kra_etims.svg",
        "title": app_title,
        "route": "/app/kra-etims",
    }
]

doc_events = {
    "Sales Invoice": {
        "on_submit": "kra_etims.etims.fiscalize_sales_invoice",
    },
}

jinja = {
    "methods": [
        "kra_etims.etims.get_qr_data_uri",
    ],
}

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["fieldname", "like", "custom_kra_%"],
            ["dt", "in", ["Sales Invoice", "Sales Invoice Item", "Item"]],
        ],
    },
]
