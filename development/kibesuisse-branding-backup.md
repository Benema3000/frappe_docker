# kibesuisse Branding Backup — Good Event demo site

Snapshot taken **2026-07-09** before switching the demo branding to SWAESS
(swiss aesthetic surgery, swaess.ch). Restore these values to switch back.

Site: `development16.localhost`

## Good Event Settings (Single)

Restore via bench console / Desk → Good Event Settings:

| Field | kibesuisse value |
|---|---|
| `client_name` | `kibesuisse` |
| `logo` | `/assets/miki_app/images/kibesuisse-logo.svg` |
| `google_fonts_url` | `https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap` |
| `default_currency` | `CHF` |
| `default_language` | `de` |
| `primary_color` | `#578D1F` |
| `primary_soft_color` | `#def8bc` |
| `secondary_color` | `#96c11f` |
| `accent_color` | `#0078bd` |
| `warning_color` | `#f39200` |
| `text_color` | `#1d1d1d` |
| `muted_bg_color` | `#f1f1f1` |
| `surface_color` | `#ffffff` |
| `border_color` | `#e4e4e4` |
| `heading_font_family` | `'Open Sans', Arial, Helvetica, sans-serif` |
| `body_font_family` | `'Open Sans', Arial, Helvetica, sans-serif` |
| `card_radius` | `12px` |
| `hero_height_desktop` | `440px` |
| `hero_height_mobile` | `560px` |
| `header_home_url` | `/lists/kursprogramm` |
| `confirmation_title` | `Teilnahmebestätigung` |
| `confirmation_attended_text` | `hat an folgender Veranstaltung teilgenommen:` |
| `confirmation_title_label` | `Titel` |
| `confirmation_date_label` | `Datum` |
| `confirmation_date_sep` | `bis` |
| `confirmation_duration_label` | `Dauer` |
| `confirmation_hours_unit` | `Stunden` |
| `confirmation_venue_label` | `Ort` |
| `confirmation_content_label` | `Inhalte` |
| `confirmation_sign_off` | `Event Team` |
| `enabled_languages` | de, fr, it (child table `Good Event Settings Language` rows) |
| `global_subsidy_coupons` | (empty) |

## Good Event Email Settings (Single) — values below are the kibesuisse originals

> The SWAESS switch changed exactly one field here: `auto_confirmation` 0 → 1
> (automatic certificate dispatch for the demo). Reset it to 0 when restoring.

| Field | Value |
|---|---|
| `auto_invoice` | 1 |
| `auto_ticket_confirmation` | 1 |
| `auto_waitlist_confirmation` | 1 |
| `auto_webinar_access` | 1 |
| `auto_survey` | 1 |
| `auto_confirmation` | 0 |
| `auto_trainer_short_notice` | 0 |
| `auto_trainer_settlement` | 0 |
| `auto_event_cancellation` | 1 |
| `auto_ticket_cancellation` | 1 |
| `pre_event_package_lead_days` | 29 |
| `trainer_short_notice_days` | 7 |
| `survey_send_hour` | 8 |

## Website Settings (Single) — unchanged reference (Goodvantage, not kibesuisse)

| Field | Value |
|---|---|
| `home_page` | `demo` |
| `app_name` | `Goodvantage` |
| `app_logo` | `/assets/good_npo/images/goodvantage-app-logo.svg` |
| `splash_image` | `/assets/good_npo/images/goodvantage-app-logo.svg` |
| `favicon` | `/assets/good_npo/images/goodvantage-app-logo.svg` |
| `website_theme` | `Standard` |

## Restore snippet

```python
import frappe
frappe.init(site="development16.localhost", sites_path="/workspace/development/frappe-bench/sites")
frappe.connect()
s = frappe.get_doc("Good Event Settings")
s.update({
	"client_name": "kibesuisse",
	"logo": "/assets/miki_app/images/kibesuisse-logo.svg",
	"google_fonts_url": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap",
	"primary_color": "#578D1F",
	"primary_soft_color": "#def8bc",
	"secondary_color": "#96c11f",
	"accent_color": "#0078bd",
	"warning_color": "#f39200",
	"text_color": "#1d1d1d",
	"muted_bg_color": "#f1f1f1",
	"surface_color": "#ffffff",
	"border_color": "#e4e4e4",
	"heading_font_family": "'Open Sans', Arial, Helvetica, sans-serif",
	"body_font_family": "'Open Sans', Arial, Helvetica, sans-serif",
	"header_home_url": "/lists/kursprogramm",
	"confirmation_sign_off": "Event Team",
})
s.save()
es = frappe.get_doc("Good Event Email Settings")
es.auto_confirmation = 0
es.save()
frappe.db.commit()
```

## ⚠️ Every `bench migrate` re-imposes kibesuisse

miki_app registers `good_event_seed_data_provider =
miki_app.good_event_seeds.get_kibesuisse_seed_data`; good_event's
`seeds._apply_event_settings` force-writes its `EVENT_SETTINGS`
(`client_name`, `logo`, `header_home_url`, languages) into Good Event Settings
on every migrate, and miki seeds can restore the kibesuisse Letter Head and
invoice print format. **After any migrate, re-apply the SWAESS demo with:**

```bash
cd /workspace/development/frappe-bench && ./env/bin/python /workspace/development/swaess-demo-reapply.py
bench --site development16.localhost clear-cache
```

(Conversely: switching back to kibesuisse is mostly just a migrate plus the
restore steps below.)

## PDF / email-footer branding (changed 2026-07-09, second pass)

The SWAESS switch also touched these shared branding records (they drive
good_event AND miki PDFs plus every outgoing email):

| Record | kibesuisse value | SWAESS demo value | Restore |
|---|---|---|---|
| Default `Letter Head` | `Ilanga` (`is_default=1`) | new `SWAESS` Letter Head is default | set `is_default=1` on `Ilanga` (auto-unsets SWAESS) |
| `Letter Head` "Miki Letter Head" content/footer | kibesuisse header/footer imgs (`{{ header_image_src or … }}`) | static SWAESS logo + address | `bench --site development16.localhost execute miki_app.correspondence_seeds.ensure_letter_head --kwargs "{'overwrite': True}"` |
| `Print Format` "Miki Sales Invoice Standard" | kibesuisse header/footer `<img>` tags | SWAESS data-URI logo + text footer (marked `SWAESS demo override`) | `bench … execute miki_app.correspondence_seeds.ensure_standard_sales_invoice_print_format --kwargs "{'overwrite': True}"` |
| `Email Account` footers (`Benediktmathis`, `_Test Email Account 1`) | kibesuisse block (`data-kibesuisse-email-footer`) | SWAESS block (`data-swaess-email-footer`) | blank the footer, then `bench … execute miki_app.correspondence_seeds.ensure_kibesuisse_email_footer_settings` (its guard skips non-empty custom footers) |
| `Good Event Settings.confirmation_bg_image` | (empty → falls back to kibesuisse `/assets/good_event/images/confirmation-bg.jpg`) | `/files/swaess-confirmation-bg.jpg` | clear the field |

Note: "Miki Dunning Standard" print format was NOT touched — dunning PDFs
would still render kibesuisse if demoed.

QR-bill page caveats (invoice PDF page 2):
- The QR page logo is hardcoded in miki_app code
  (`receivables._render_letter_head` → `_image_data_uri(MIKI_HEADER_IMAGE_ASSET)`,
  template `miki_qr_bill_page.html`). No DB lever exists; the SWAESS demo sends
  patched `miki_app.receivables._image_data_uri` **in-process only**. Invoice
  PDFs generated from Desk or by future background workers will show the
  kibesuisse logo on the QR page again. Nothing to restore — the patch never
  persisted.
- The QR creditor ("Ilanga, Schellenrainstrasse, 6210 Sursee", IBAN CH44 …)
  comes from the site's default Company / QR bank account and was left
  unchanged.

(SWAESS demo events / the `swaess` Good Event List can stay — they are only
reachable through their own list page — or delete the Good Events named
`SAM Jahreskongress*`, `Industrie Workshop*`, `Advanced Training Day*`,
`Injection Academy*` plus the `swaess` Good Event List to remove them.)
