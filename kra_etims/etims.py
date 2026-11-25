import frappe
from frappe import _
from vscu_sdk import ERPNextVscuConnector, Vscu, VscuException

SETTINGS_DOCTYPE = "KRA eTIMS Settings"


def get_vscu_client(settings=None) -> Vscu:
    settings = settings or frappe.get_single(SETTINGS_DOCTYPE)
    if not settings.vscu_url:
        frappe.throw(_("Configure VSCU Server URL in KRA eTIMS Settings first."))

    return Vscu({
        "base_url": settings.vscu_url,
        "timeout": float(settings.timeout or 30.0),
        "cf_access_client_id": settings.get_password("cf_client_id", raise_exception=False),
        "cf_access_client_secret": settings.get_password("cf_client_secret", raise_exception=False),
    })


def _get_company_pin(company: str) -> str:
    pin = frappe.db.get_value("Company", company, "tax_id")
    if not pin:
        frappe.throw(_("Set the KRA PIN in Company {0} -> Tax ID.").format(company))
    return str(pin).strip()


def _next_invc_no() -> int:
    """Atomically reserve the next sequential fiscal invoice number.
    Rolls back automatically if Sales Invoice submission fails."""
    row = frappe.db.sql(
        "select value from `tabSingles` where doctype=%s and field='next_invc_no' for update",
        SETTINGS_DOCTYPE,
    )
    current = int(row[0][0]) if row and row[0][0] else 1
    frappe.db.set_single_value(SETTINGS_DOCTYPE, "next_invc_no", current + 1)
    return current


def _build_qr_url(tin: str, bhf_id: str, rcpt_sign: str, is_sandbox: bool) -> str:
    if not rcpt_sign:
        return ""
    if hasattr(Vscu, "build_qr_code_url"):
        return Vscu.build_qr_code_url(tin, bhf_id, rcpt_sign, sandbox=is_sandbox)
    host = "etims-sbx.kra.go.ke" if is_sandbox else "etims.kra.go.ke"
    return f"https://{host}/common/link/etims/receipt/indexEtimsReceiptData?Data={tin}{bhf_id}{rcpt_sign}"


def fiscalize_sales_invoice(doc, method=None):
    """Hooked to Sales Invoice.on_submit."""
    settings = frappe.get_single(SETTINGS_DOCTYPE)
    if not settings.enabled:
        return

    company_pin = _get_company_pin(doc.company)
    bhf_id = doc.get("custom_kra_bhf_id") or settings.bhf_id or "00"

    if doc.is_return:
        if not doc.return_against:
            frappe.throw(_("Credit Note must reference an original Sales Invoice (Return Against)."))
        org_invc_no = frappe.db.get_value("Sales Invoice", doc.return_against, "custom_kra_invc_no")
        if not org_invc_no:
            frappe.throw(
                _("Original Sales Invoice {0} has not been fiscalized yet.").format(doc.return_against)
            )
        doc.custom_kra_org_invc_no = str(org_invc_no)

    invc_no = _next_invc_no()
    client = get_vscu_client(settings)
    connector = ERPNextVscuConnector(client, default_bhf_id=bhf_id)

    try:
        res = connector.fiscalize_invoice(
            doc=doc,
            company_pin=company_pin,
            bhf_id=bhf_id,
            fiscal_seq_no=invc_no,
        )
    except VscuException as exc:
        frappe.throw(_("KRA eTIMS VSCU connection error: {0}").format(exc))

    if res.get("resultCd") != "000":
        frappe.throw(
            _("KRA eTIMS rejected this invoice: {0} (code {1})").format(
                res.get("resultMsg") or "Unknown error",
                res.get("resultCd"),
            )
        )

    data = res.get("data") or {}
    rcpt_sign = data.get("rcptSign") or ""
    qr_url = data.get("qrCodeUrl") or _build_qr_url(
        tin=company_pin,
        bhf_id=bhf_id,
        rcpt_sign=rcpt_sign,
        is_sandbox=(settings.environment == "Sandbox"),
    )

    doc.db_set(
        {
            "custom_kra_invc_no": invc_no,
            "custom_kra_org_invc_no": doc.get("custom_kra_org_invc_no"),
            "custom_kra_sdc_id": data.get("sdcId"),
            "custom_kra_mrc_no": data.get("mrcNo"),
            "custom_kra_rcpt_sign": rcpt_sign,
            "custom_kra_intrl_data": data.get("intrlData"),
            "custom_kra_qr_code": qr_url,
            "custom_kra_fiscal_status": "Fiscalized",
        },
        update_modified=False,
    )


@frappe.whitelist()
def initialize_device():
    """One-time VSCU device initialization from KRA eTIMS Settings."""
    frappe.only_for(("System Manager", "Accounts Manager"))
    settings = frappe.get_single(SETTINGS_DOCTYPE)
    company = settings.company or frappe.defaults.get_global_default("company")
    if not company:
        frappe.throw(_("Select a Default Company in KRA eTIMS Settings first."))

    tin = _get_company_pin(company)
    bhf_id = settings.bhf_id or "00"
    dvc_srl_no = settings.dvc_srl_no or "SANDBOX-SRL-001"
    client = get_vscu_client(settings)

    try:
        if hasattr(client, "initialize"):
            return client.initialize(tin=tin, bhf_id=bhf_id, dvc_srl_no=dvc_srl_no)
        return client.sales().request(
            "POST",
            "initializer/selectInitInfo",
            data={"tin": tin, "bhfId": bhf_id, "dvcSrlNo": dvc_srl_no},
        )
    except VscuException as exc:
        frappe.throw(_("VSCU initialization failed: {0}").format(exc))


@frappe.whitelist()
def test_connection():
    """Verify VSCU reachability by syncing standard KRA lookup codes."""
    frappe.only_for(("System Manager", "Accounts Manager"))
    settings = frappe.get_single(SETTINGS_DOCTYPE)
    company = settings.company or frappe.defaults.get_global_default("company")
    if not company:
        frappe.throw(_("Select a Default Company in KRA eTIMS Settings first."))

    tin = _get_company_pin(company)
    bhf_id = settings.bhf_id or "00"
    client = get_vscu_client(settings)

    try:
        return client.sales().request(
            "POST",
            "code/selectCodes",
            data={"tin": tin, "bhfId": bhf_id, "lastReqDt": "20200101000000"},
        )
    except VscuException as exc:
        frappe.throw(_("VSCU connection test failed: {0}").format(exc))
