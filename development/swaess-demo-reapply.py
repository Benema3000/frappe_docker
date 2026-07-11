"""Re-apply SWAESS demo branding after a `bench migrate`.

miki_app's `good_event_seed_data_provider` re-imposes kibesuisse values
(client_name, logo, header_home_url) on Good Event Settings during every
migrate, and miki seeds can restore the kibesuisse Letter Head / invoice
print format. This script idempotently re-applies every SWAESS surface.

Run:  cd /workspace/development/frappe-bench && ./env/bin/python /workspace/development/swaess-demo-reapply.py
Switch back to kibesuisse: see kibesuisse-branding-backup.md (a migrate
also restores most of it automatically).
"""

import base64
import os

import frappe

os.chdir("/workspace/development/frappe-bench/sites")
frappe.init(site="development16.localhost", sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

LOGO_PATH = "development16.localhost/public/files/swaess-logo.png"

# ---------------------------------------------------------------- 1. Good Event Settings
settings = frappe.get_doc("Good Event Settings")
settings.update(
	{
		"client_name": "SWAESS – Swiss Aesthetic Surgery",
		"logo": "/files/swaess-logo.png",
		"favicon": "/files/swaess-logo.png",
		"google_fonts_url": "https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Inter:wght@400;600&display=swap",
		"heading_font_family": "'Barlow', Helvetica, Arial, sans-serif",
		"body_font_family": "'Inter', Helvetica, Arial, sans-serif",
		"primary_color": "#547FA8",
		"primary_soft_color": "#dce9f5",
		"secondary_color": "#70A9E0",
		"accent_color": "#385470",
		"warning_color": "#D49D42",
		"text_color": "#2F2F2E",
		"muted_bg_color": "#F5F5F3",
		"surface_color": "#ffffff",
		"border_color": "#EAEAE8",
		"header_home_url": "/lists/swaess",
		"confirmation_bg_image": "/files/swaess-confirmation-bg.jpg",
		"confirmation_sign_off": "SWAESS Event Team",
	}
)
settings.save(ignore_permissions=True)
print("[ok] Good Event Settings")

email_settings = frappe.get_doc("Good Event Email Settings")
if not email_settings.auto_confirmation:
	email_settings.auto_confirmation = 1
	email_settings.save(ignore_permissions=True)
print("[ok] auto_confirmation = 1")

# ---------------------------------------------------------------- 2. default Letter Head "SWAESS"
LH_CONTENT = (
	'<div style="display:flex; align-items:flex-end; justify-content:space-between; '
	'padding:8px 0 10px; border-bottom:2px solid #547FA8;">'
	'<img src="/files/swaess-logo.png" alt="SWAESS" style="height:64px; width:auto;">'
	'<div style="text-align:right; font-size:8pt; color:#666; line-height:1.4;">'
	"SWAESS – Swiss Aesthetic Surgery<br>sekretariat@swaess.ch · www.swaess.ch</div></div>"
)
LH_FOOTER = (
	'<div style="border-top:1px solid #EAEAE8; padding:8px 0; margin-top:20px; '
	'font-size:7pt; color:#999; text-align:center;">'
	"SWAESS – Swiss Aesthetic Surgery · Schweizerische Gesellschaft für Ästhetische Chirurgie · "
	"sekretariat@swaess.ch · www.swaess.ch</div>"
)
if frappe.db.exists("Letter Head", "SWAESS"):
	frappe.db.set_value(
		"Letter Head",
		"SWAESS",
		{"content": LH_CONTENT, "footer": LH_FOOTER, "disabled": 0},
		update_modified=False,
	)
else:
	lh = frappe.new_doc("Letter Head")
	lh.letter_head_name = "SWAESS"
	lh.source = "HTML"
	lh.footer_source = "HTML"
	lh.content = LH_CONTENT
	lh.footer = LH_FOOTER
	lh.insert(ignore_permissions=True)
if frappe.db.get_value("Letter Head", {"is_default": 1}, "name") != "SWAESS":
	doc = frappe.get_doc("Letter Head", "SWAESS")
	doc.is_default = 1
	doc.save(ignore_permissions=True)
print("[ok] default Letter Head = SWAESS")

# ---------------------------------------------------------------- 3. Miki Letter Head -> static SWAESS
with open(LOGO_PATH, "rb") as fh:
	logo_b64 = base64.b64encode(fh.read()).decode()
miki_content = (
	f'<img src="data:image/png;base64,{logo_b64}" alt="SWAESS" '
	'style="display:block;width:26.8mm;height:auto;margin:0;padding:0;">'
)
miki_footer = (
	'<div style="font-family:Arial,Helvetica,sans-serif;font-size:8pt;color:#444;line-height:1.45;">'
	"<strong>SWAESS – Swiss Aesthetic Surgery</strong><br>"
	"Schweizerische Gesellschaft für Ästhetische Chirurgie<br>"
	"sekretariat@swaess.ch, www.swaess.ch</div>"
)
if frappe.db.exists("Letter Head", "Miki Letter Head"):
	frappe.db.set_value(
		"Letter Head",
		"Miki Letter Head",
		{"content": miki_content, "footer": miki_footer},
		update_modified=False,
	)
	print("[ok] Miki Letter Head -> SWAESS")

# ---------------------------------------------------------------- 4. Miki Sales Invoice print format imgs
PF = "Miki Sales Invoice Standard"
html = frappe.db.get_value("Print Format", PF, "html") or ""
header_img_old = (
	"""<img src="{{ header_image_src or '/assets/miki_app/images/kibesuisse-header.jpg' }}" alt="kibesuisse">"""
)
footer_img_old = (
	"""<img src="{{ footer_image_src or '/assets/miki_app/images/kibesuisse-footer.jpg' }}" alt="kibesuisse">"""
)
header_img_new = (
	f'<img src="data:image/png;base64,{logo_b64}" alt="SWAESS" '
	'style="display:block;width:26.8mm;height:auto;margin:0;padding:0;">'
)
marker = "<!-- SWAESS demo override; original used header_image_src / footer_image_src -->"
if "SWAESS demo override" in html:
	print("[ok] print format already SWAESS")
elif header_img_old in html:
	html = html.replace(header_img_old, header_img_new + marker)
	html = html.replace(footer_img_old, miki_footer)
	frappe.db.set_value("Print Format", PF, "html", html, update_modified=False)
	print("[ok] print format imgs -> SWAESS")
else:
	print("[??] print format: kibesuisse img tags not found and no SWAESS marker — check manually")

# ---------------------------------------------------------------- 5. Email Account footers
SWAESS_EMAIL_FOOTER = """
<div data-swaess-email-footer="true" style="margin-top:24px; padding-top:12px; border-top:1px solid #EAEAE8; font-family:Arial, Helvetica, sans-serif; font-size:10pt; color:#444; line-height:1.5;">
	<p style="margin:0 0 4px; font-weight:600;">SWAESS – Swiss Aesthetic Surgery</p>
	<p style="margin:0; color:#666;">Schweizerische Gesellschaft für Ästhetische Chirurgie<br>Swiss Society for Aesthetic Surgery</p>
	<p style="margin:8px 0 0; color:#666;">sekretariat@swaess.ch, www.swaess.ch</p>
</div>
"""
for account_name in frappe.get_all("Email Account", filters={"enable_outgoing": 1}, pluck="name"):
	current = frappe.db.get_value("Email Account", account_name, "footer") or ""
	if 'data-kibesuisse-email-footer="true"' in current:
		frappe.db.set_value("Email Account", account_name, "footer", SWAESS_EMAIL_FOOTER, update_modified=False)
		print("[ok] email footer -> SWAESS on", account_name)

frappe.db.commit()
frappe.clear_cache()
print("DONE — hard-reload /lists/swaess")
