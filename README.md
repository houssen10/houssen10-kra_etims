# KRA eTIMS (VSCU) for ERPNext

Frappe / ERPNext app that fiscalizes **Sales Invoices** and **Credit Notes** on submit via KRA eTIMS **VSCU v2.0.6** using `vscu-python-sdk`.

## 1. Install on Frappe Cloud

1. Push this folder to a GitHub repository (e.g. `https://github.com/houssen10/houssen10-kra_etims`).
2. In **Frappe Cloud Dashboard → Your Private Bench → Apps → Add App**, select this repo and deploy the bench.
3. On your site, click **Apps → Install App → KRA eTIMS**.

## 2. Expose Local VSCU Sandbox to Frappe Cloud

Because Frappe Cloud cannot reach `127.0.0.1:8088` on your local machine, expose it over HTTPS with Cloudflare Tunnel:

```bash
brew install cloudflared
cloudflared tunnel --url http://127.0.0.1:8088
```

Copy the `https://....trycloudflare.com` URL printed by `cloudflared`. (For production, use a named Cloudflare Tunnel + Cloudflare Access Service Token.)

## 3. Configure in ERPNext Desk

1. Open **Company → Your Company** and set **Tax ID** to your KRA PIN (for the local sandbox, use `P000000001A`).
2. Open **KRA eTIMS Settings**:
   - **Environment**: `Sandbox`
   - **Default Company**: `<Your Company>`
   - **VSCU Server URL**: `https://<your-tunnel>.trycloudflare.com/`
   - **Branch ID**: `00`
   - **Device Serial Number**: `SANDBOX-SRL-001`
   - **Next Fiscal Invoice Number**: `1` (or `lastInvcNo + 1` from `http://127.0.0.1:8050/sandbox/state`)
   - Tick **Enabled** and click **Save**.
3. Click **Actions → Initialize VSCU Device**, then **Actions → Test Connection (Sync Codes)**. Both should return `000`.
4. Submit a Sales Invoice (with VAT marked **Included in Basic Rate**) and confirm the **KRA eTIMS (VSCU)** section is populated with `KRA Receipt Signature`, `KRA SDC ID`, and `KRA QR Verification URL`.
