"""Seed SWAESS (swaess.ch) demo branding + events on development16.localhost.

Idempotent: safe to rerun. No code changes — records only.
"""

import frappe

frappe.init(site="development16.localhost", sites_path="/workspace/development/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

STREAM = "SWAESS"


# ---------------------------------------------------------------- files
def upload(local_path, fname):
	url = f"/files/{fname}"
	if frappe.db.exists("File", {"file_url": url}):
		return url
	with open(local_path, "rb") as fh:
		data = fh.read()
	frappe.get_doc(
		{"doctype": "File", "file_name": fname, "is_private": 0, "content": data}
	).insert(ignore_permissions=True)
	return url


logo_url = upload("/tmp/swaess_logo_color.png", "swaess-logo.png")
img_kongress = upload("/tmp/swaess_img/kongress.jpg", "swaess-jahreskongress.jpg")
img_workshop = upload("/tmp/swaess_img/training.jpg", "swaess-industrie-workshop.jpg")
img_training = upload("/tmp/swaess_img/injection.jpg", "swaess-advanced-training-day.jpg")
img_academy = upload("/tmp/swaess_img/alt_c37b09.jpg", "swaess-injection-academy.jpg")
img_gala = upload("/tmp/swaess_img/gala.jpg", "swaess-galadiner.jpg")
img_hero = upload("/tmp/swaess_img/hero.jpg", "swaess-hero.jpg")
print("files ok")

# ---------------------------------------------------------------- branding
settings = frappe.get_doc("Good Event Settings")
settings.update(
	{
		"client_name": "SWAESS – Swiss Aesthetic Surgery",
		"logo": logo_url,
		"favicon": logo_url,
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
		"confirmation_sign_off": "SWAESS Event Team",
	}
)
settings.save(ignore_permissions=True)

email_settings = frappe.get_doc("Good Event Email Settings")
email_settings.auto_confirmation = 1  # Zertifikatsversand automatisch
email_settings.save(ignore_permissions=True)
print("branding ok")

# ---------------------------------------------------------------- sponsors (Customers)
territory = (
	frappe.db.get_single_value("Selling Settings", "territory")
	or ("All Territories" if frappe.db.exists("Territory", "All Territories") else None)
)
group = (
	"Commercial"
	if frappe.db.exists("Customer Group", "Commercial")
	else frappe.db.get_single_value("Selling Settings", "customer_group")
)
sponsors = ["SwissDerm Pharma AG", "Helvetia Medical Systems SA", "AlpineAesthetics GmbH"]
for name in sponsors:
	if not frappe.db.exists("Customer", {"customer_name": name}):
		doc = frappe.new_doc("Customer")
		doc.customer_name = name
		doc.customer_type = "Company"
		if group:
			doc.customer_group = group
		if territory:
			doc.territory = territory
		doc.insert(ignore_permissions=True)
sponsor_main = frappe.db.get_value("Customer", {"customer_name": sponsors[0]})
print("sponsors ok")

# ---------------------------------------------------------------- type
if not frappe.db.exists("Good Event Type", "SWAESS"):
	frappe.get_doc(
		{"doctype": "Good Event Type", "code": "SWAESS", "title": "SWAESS Event"}
	).insert(ignore_permissions=True)

# ---------------------------------------------------------------- venues
VENUES = [
	("Kongresshaus Zürich", "Claridenstrasse 5\n8002 Zürich", "ZH"),
	("Inselspital Bern – Auditorium", "Freiburgstrasse 18\n3010 Bern", "BE"),
	("SWAESS Academy Lab Genève", "Rue de Lausanne 45\n1201 Genève", "GE"),
]
for title, address, canton in VENUES:
	if not frappe.db.exists("Good Event Venue", title):
		frappe.get_doc(
			{"doctype": "Good Event Venue", "title": title, "address": address, "canton": canton}
		).insert(ignore_permissions=True)
print("venues ok")


# ---------------------------------------------------------------- pricing
def pricing_profile(title, tiers):
	if frappe.db.exists("Good Event Pricing Profile", {"title": title}):
		return frappe.db.get_value("Good Event Pricing Profile", {"title": title})
	doc = frappe.new_doc("Good Event Pricing Profile")
	doc.title = title
	doc.currency = "CHF"
	for i, (code, label, price, default, member, desc) in enumerate(tiers):
		doc.append(
			"tiers",
			{
				"tariff_code": code,
				"title": label,
				"price": price,
				"is_default": default,
				"is_member_price": member,
				"description": desc,
				"sort_order": i,
			},
		)
	doc.insert(ignore_permissions=True)
	return doc.name


pp_kongress = pricing_profile(
	"SAM Jahreskongress 2026",
	[
		("standard", "Nicht-Mitglied", 650, 1, 0, "Fachärztinnen und Fachärzte ohne SWAESS-Mitgliedschaft"),
		("member", "SWAESS Mitglied", 450, 0, 1, "Reduzierter Tarif für SWAESS-Mitglieder"),
		("resident", "Resident / Assistenzarzt:ärztin", 250, 0, 0, "In Weiterbildung (Nachweis erforderlich)"),
		("begleitperson", "Begleitperson (nur Galadiner)", 150, 0, 0, "Begleitperson für Galadiner & Networking-Abend"),
		("industrie", "Industrie / Aussteller", 900, 0, 0, "Vertreter:innen der Industrie"),
	],
)
pp_training = pricing_profile(
	"Advanced Training Day 2026",
	[
		("standard", "Nicht-Mitglied", 480, 1, 0, ""),
		("member", "SWAESS Mitglied", 380, 0, 1, ""),
		("resident", "Resident / Assistenzarzt:ärztin", 240, 0, 0, "In Weiterbildung (Nachweis erforderlich)"),
	],
)
pp_academy = pricing_profile(
	"Injection Academy 2026",
	[
		("standard", "Nicht-Mitglied", 890, 1, 0, "Inkl. Kursmaterial und Hands-on-Training"),
		("member", "SWAESS Mitglied", 690, 0, 1, "Inkl. Kursmaterial und Hands-on-Training"),
	],
)
print("pricing ok")

# ---------------------------------------------------------------- registration template
TPL = "SWAESS Anmeldung"
if not frappe.db.exists("Good Event Registration Template", TPL):
	tpl = frappe.new_doc("Good Event Registration Template")
	tpl.title = TPL
	tpl.show_organization_booking = 0
	tpl.append("general_fields", {"field_key": "invoice_recipient", "mandatory": 1, "sort_order": 0})
	tpl.append(
		"general_fields",
		{"field_key": "remarks", "label": "Bemerkungen", "mandatory": 0, "sort_order": 1},
	)
	for i, row in enumerate(
		[
			{"field_key": "salutation", "label": "Anrede", "mandatory": 1},
			{"field_key": "tariff", "label": "Ticketkategorie", "mandatory": 1},
			{"field_key": "phone", "label": "Telefon", "fieldtype": "Phone", "mandatory": 0},
			{"field_key": "address", "label": "Rechnungsadresse", "mandatory": 1, "conditional": 1},
			{
				"field_key": "Custom",
				"label": "FMH / GLN-Nummer",
				"fieldtype": "Data",
				"mandatory": 0,
				"show_in_participant_list": 1,
			},
			{
				"field_key": "Custom",
				"label": "Teilnahme Galadiner",
				"fieldtype": "Check",
				"mandatory": 0,
				"show_in_participant_list": 1,
			},
			{
				"field_key": "Custom",
				"label": "Diätwünsche / Allergien",
				"fieldtype": "Data",
				"mandatory": 0,
			},
		]
	):
		row["sort_order"] = i
		tpl.append("ticket_fields", row)
	tpl.insert(ignore_permissions=True)
print("template ok")


# ---------------------------------------------------------------- events
def make_event(spec):
	existing = frappe.db.get_value("Good Event", {"route": spec["route"]})
	if existing:
		return existing
	doc = frappe.new_doc("Good Event")
	sections = spec.pop("content_sections", [])
	overrides = spec.pop("email_overrides", [])
	doc.update(spec)
	doc.event_type = "SWAESS"
	doc.event_language = "de"
	doc.catalog_stream = STREAM
	doc.visibility_mode = "Public"
	doc.public_link_type = "Native"
	doc.registration_template = TPL
	doc.workflow_state = "Draft"
	doc.is_published = 0
	for i, s in enumerate(sections):
		s.setdefault("sort_order", i)
		s.setdefault("show_on_public_page", 1)
		doc.append("content_sections", s)
	for o in overrides:
		doc.append("email_overrides", o)
	doc.insert(ignore_permissions=True)
	frappe.db.set_value(
		"Good Event",
		doc.name,
		{"workflow_state": "Open for Registration", "is_published": 1, "show_in_catalog": 1},
		update_modified=False,
	)
	return doc.name


ev_kongress = make_event(
	{
		"title": "SAM Jahreskongress 2026",
		"route": "sam-jahreskongress-2026",
		"start_date": "2026-09-24",
		"end_date": "2026-09-25",
		"start_time": "08:30:00",
		"end_time": "17:30:00",
		"venue_record": "Kongresshaus Zürich",
		"medium": "In Person",
		"max_participants_total": 100,
		"waitlist_enabled": 1,
		"pricing_mode": "Paid",
		"pricing_profile": pp_kongress,
		"pay_later": 1,
		"duration_hours": 16,
		"card_image": img_kongress,
		"banner_image": img_kongress,
		"short_description": (
			"Der jährliche Treffpunkt der Schweizer ästhetischen Chirurgie: zwei Tage "
			"Wissenschaft, Live-Demonstrationen und Networking mit über 100 Teilnehmenden, "
			"Galadiner inklusive."
		),
		"survey_url": "https://survey.swaess.ch/sam-jahreskongress-2026",
		"content_sections": [
			{
				"section_key": "programm",
				"label": "Programm",
				"content": (
					"<p><strong>Tag 1 – Donnerstag, 24. September 2026</strong></p>"
					"<ul><li>08:30 Registrierung &amp; Welcome Coffee</li>"
					"<li>09:15 Keynote: State of the Art in Facial Surgery</li>"
					"<li>11:00 Live-OP-Übertragung mit Panel-Diskussion</li>"
					"<li>14:00 Freie Vorträge &amp; Abstract Session</li>"
					"<li>17:30 Apéro in der Industrie-Ausstellung</li>"
					"<li>19:30 <strong>Galadiner &amp; Networking-Abend</strong></li></ul>"
					"<p><strong>Tag 2 – Freitag, 25. September 2026</strong></p>"
					"<ul><li>09:00 Komplikationsmanagement: Fallbesprechungen</li>"
					"<li>11:00 Rhinoplastik-Symposium</li>"
					"<li>14:00 Body Contouring Update</li>"
					"<li>16:30 Preisverleihung Best Abstract &amp; Farewell</li></ul>"
				),
			},
			{
				"section_key": "schwerpunkte",
				"label": "Schwerpunkte",
				"content": (
					"<ul><li>Gesichtschirurgie und Rhinoplastik</li>"
					"<li>Komplikationsmanagement in der ästhetischen Chirurgie</li>"
					"<li>Body Contouring und regenerative Verfahren</li>"
					"<li>Patientensicherheit und Qualitätsstandards</li></ul>"
				),
				"show_in_certificate": 1,
			},
			{
				"section_key": "galadiner",
				"label": "Galadiner & Networking",
				"content": (
					f'<img src="{img_gala}" alt="Galadiner" '
					'style="width:100%;max-height:340px;object-fit:cover;border-radius:12px;margin-bottom:12px">'
					"<p>Der Kongress-Höhepunkt: Galadiner am Donnerstagabend im Kongresshaus "
					"Zürich mit Blick auf den See. Begleitpersonen sind herzlich willkommen "
					"(separate Ticketkategorie <em>Begleitperson</em>). Bitte Teilnahme und "
					"Diätwünsche bei der Anmeldung angeben.</p>"
				),
			},
			{
				"section_key": "sponsoren",
				"label": "Sponsoren & Partner",
				"content": (
					"<p>Wir danken unseren Partnern für die Unterstützung des SAM Jahreskongresses 2026:</p>"
					"<p><strong>Platin-Sponsor:</strong> SwissDerm Pharma AG<br>"
					"<strong>Gold-Sponsor:</strong> Helvetia Medical Systems SA<br>"
					"<strong>Silber-Sponsor:</strong> AlpineAesthetics GmbH</p>"
					"<p>Interessiert an einem Sponsoring-Paket? Kontaktieren Sie uns unter "
					'<a href="mailto:sponsoring@swaess.ch">sponsoring@swaess.ch</a>.</p>'
				),
			},
		],
		"email_overrides": [
			{
				"flow": "ticket_confirmation",
				"custom_message": (
					"<p>Wir freuen uns, Sie am SAM Jahreskongress 2026 begrüssen zu dürfen. "
					"Denken Sie an das Galadiner am Donnerstagabend – der Dresscode ist "
					"Business/Cocktail. Begleitpersonen benötigen ein eigenes Ticket.</p>"
				),
				"attach_calendar": 1,
			}
		],
	}
)

ev_workshop = make_event(
	{
		"title": "Industrie Workshop: Injectables & Filler Innovationen",
		"route": "industrie-workshop-filler-2026",
		"start_date": "2026-10-15",
		"end_date": "2026-10-15",
		"start_time": "13:30:00",
		"end_time": "17:30:00",
		"venue_record": "Inselspital Bern – Auditorium",
		"medium": "In Person",
		"max_participants_total": 16,
		"waitlist_enabled": 1,
		"pricing_mode": "Free",
		"bill_to_organizer_only": 1,
		"organizer_customer": sponsor_main,
		"duration_hours": 4,
		"card_image": img_workshop,
		"banner_image": img_workshop,
		"short_description": (
			"Exklusiver Industrie-Workshop mit streng limitierter Teilnehmerzahl (16 Plätze). "
			"Gesponsert von SwissDerm Pharma AG – Teilnahme kostenlos, Warteliste verfügbar."
		),
		"survey_url": "https://survey.swaess.ch/industrie-workshop-filler-2026",
		"content_sections": [
			{
				"section_key": "beschreibung",
				"label": "Beschreibung",
				"content": (
					"<p>In Kleingruppen stellen Expertinnen und Experten die neuesten "
					"Filler-Generationen vor – inklusive Hands-on-Stationen und "
					"Produktvergleich. Die Teilnehmerzahl ist auf 16 Personen limitiert, "
					"damit jede:r selbst injizieren kann. Bei Überbuchung führen wir eine "
					"automatische Warteliste.</p>"
				),
			},
			{
				"section_key": "sponsor",
				"label": "Sponsor",
				"content": (
					"<p>Dieser Workshop wird vollständig von <strong>SwissDerm Pharma AG</strong> "
					"getragen. Die Teilnahme ist für SWAESS-Mitglieder kostenlos; die "
					"Verrechnung erfolgt direkt an den Sponsor.</p>"
				),
			},
		],
	}
)

ev_training = make_event(
	{
		"title": "Advanced Training Day 2026",
		"route": "advanced-training-day-2026",
		"start_date": "2026-10-29",
		"end_date": "2026-10-29",
		"start_time": "08:30:00",
		"end_time": "17:00:00",
		"venue_record": "Inselspital Bern – Auditorium",
		"medium": "In Person",
		"max_participants_total": 60,
		"waitlist_enabled": 1,
		"pricing_mode": "Paid",
		"pricing_profile": pp_training,
		"pay_later": 1,
		"duration_hours": 8,
		"card_image": img_training,
		"banner_image": img_training,
		"short_description": (
			"Ganztägiges Advanced Training für Fortgeschrittene – 60 Plätze, mit "
			"Teilnahmezertifikat (8 Credits) und automatischem Zertifikatsversand."
		),
		"survey_url": "https://survey.swaess.ch/advanced-training-day-2026",
		"content_sections": [
			{
				"section_key": "beschreibung",
				"label": "Beschreibung",
				"content": (
					"<p>Der Advanced Training Day vertieft chirurgische Techniken in "
					"Theorie und Praxis: Kadaver-Demonstrationen, Video-Sessions und "
					"interaktive Falldiskussionen mit erfahrenen Operateuren.</p>"
				),
			},
			{
				"section_key": "inhalte",
				"label": "Inhalte",
				"content": (
					"<ul><li>Anatomie-Refresher für Gesichts- und Halschirurgie</li>"
					"<li>Fadenlifting und minimal-invasive Techniken</li>"
					"<li>Revisions-Rhinoplastik: Fallstricke und Lösungen</li>"
					"<li>Perioperatives Management und Patientenaufklärung</li></ul>"
				),
				"show_in_certificate": 1,
			},
		],
	}
)

ev_academy = make_event(
	{
		"title": "Injection Academy 2026",
		"route": "injection-academy-2026",
		"start_date": "2026-11-12",
		"end_date": "2026-11-12",
		"start_time": "09:00:00",
		"end_time": "17:00:00",
		"venue_record": "SWAESS Academy Lab Genève",
		"medium": "In Person",
		"max_participants_total": 20,
		"waitlist_enabled": 1,
		"pricing_mode": "Paid",
		"pricing_profile": pp_academy,
		"pay_later": 1,
		"duration_hours": 7.5,
		"card_image": img_academy,
		"banner_image": img_academy,
		"short_description": (
			"Intensives Hands-on-Training für Botulinum und Filler in kleiner Gruppe – "
			"maximal 20 Teilnehmende, inklusive Zertifikat und Post-Event-Umfrage."
		),
		"survey_url": "https://survey.swaess.ch/injection-academy-2026",
		"content_sections": [
			{
				"section_key": "beschreibung",
				"label": "Beschreibung",
				"content": (
					"<p>Die Injection Academy ist das Hands-on-Format der SWAESS: Unter "
					"1:4-Betreuung trainieren Sie Injektionstechniken an Modellen und "
					"Proband:innen. Die Gruppengrösse ist auf 20 Personen beschränkt – "
					"frühzeitige Anmeldung empfohlen, Warteliste verfügbar.</p>"
				),
			},
			{
				"section_key": "inhalte",
				"label": "Inhalte",
				"content": (
					"<ul><li>Injektionsanatomie und Gefahrenzonen</li>"
					"<li>Botulinumtoxin: Indikationen und Dosierung</li>"
					"<li>Hyaluronsäure-Filler: Techniken und Produktwahl</li>"
					"<li>Notfallmanagement bei vaskulären Komplikationen</li></ul>"
				),
				"show_in_certificate": 1,
			},
		],
	}
)
print("events ok:", ev_kongress, ev_workshop, ev_training, ev_academy)

# ---------------------------------------------------------------- list page
LIST_TITLE = "SWAESS Events"
if not frappe.db.exists("Good Event List", LIST_TITLE):
	lst = frappe.new_doc("Good Event List")
	lst.title = LIST_TITLE
	lst.route = "/lists/swaess"
	lst.language = "de"
	lst.catalog_stream = STREAM
	lst.card_layout = "Grid"
	lst.hero_image = img_hero
	lst.intro = (
		"Kongresse, Trainings und Workshops der Swiss Aesthetic Surgery Society: "
		"vom SAM Jahreskongress bis zur Injection Academy – Fortbildung auf höchstem Niveau."
	)
	lst.expose_text_search = 1
	lst.expose_date_filter = 1
	lst.expose_region_filter = 0
	lst.expose_audience_segment_filter = 0
	lst.expose_category_filter = 0
	lst.expose_catalog_stream_filter = 0
	lst.sort_by = "start_date"
	lst.sort_order = "ASC"
	lst.append(
		"highlights",
		{
			"event": ev_kongress,
			"note_override": (
				"Jetzt anmelden: der grösste Schweizer Fachkongress für ästhetische "
				"Chirurgie – mit Galadiner, Industrie-Ausstellung und Best-Abstract-Award."
			),
		},
	)
	lst.append(
		"highlights",
		{
			"event": ev_academy,
			"note_override": "Nur 20 Plätze: Hands-on-Injektionstraining mit 1:4-Betreuung.",
		},
	)
	lst.insert(ignore_permissions=True)
print("list ok")

frappe.db.commit()
print("DONE")
