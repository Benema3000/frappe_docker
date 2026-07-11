# good_event — SEO Embedding into TYPO3 / WordPress

**Status:** Foundation built, tested, committed, CI green. Not yet deployed/wired to the live kibesuisse.ch TYPO3 site.
**Last updated:** 2026-07-11
**Owner context:** benediktmathis@gmail.com

Resumable handoff for embedding good_event's public event pages into a host CMS
(kibesuisse.ch = **TYPO3 v12/v13**, and any WordPress site) so they **rank for
SEO at the host URL**.

---

## 1. Goal

Show good_event's catalogue + event pages on kibesuisse.ch (and potentially
WordPress sites) such that Google indexes and ranks them **at the host domain**,
not on the good_event/Frappe host. The existing client-side `public/js/embed.js`
does **not** achieve this — a crawler of the host page sees an empty `<div>`
because the content is fetched with JS after load. The fix is **server-side**
inclusion.

## 2. Decisions locked (do not re-litigate)

| Decision | Choice | Why |
|---|---|---|
| Render model | **Server-side fragment include** ("we use our render") | good_event serves finished HTML; host emits it in its initial response → crawlable. Not a native rebuild (would duplicate all card/list/topic markup). |
| Client | **One portable PHP script** (any TYPO3 version + WordPress + plain PHP) | Not a TYPO3-version-specific extension. ~95% framework-free core; thin adapters. |
| Signup / payment | **Stays on good_event** (detail CTA links out) | A signup form never ranks, so embedding it adds captcha re-keying + Payrexx return-URL + cross-origin state for zero SEO gain. |
| Chrome | Fragment is `<main>` only — **no header/footer/breadcrumbs** | Host provides its own shell. good_event feeds `meta.breadcrumbs`; host renders native breadcrumbs. |
| TYPO3 version | kibesuisse.ch is **v12 or v13** (`/_assets/` layout, `x-typo3-*` headers) | Made moot by the version-agnostic PHP (`userFunc` API stable v8→v13). |

## 3. Architecture — three layers

```
Browser ─▶ kibesuisse.ch/kurse/injection-academy-2026
   Host (TYPO3/WP/PHP, server-side) ──▶ GoodEventEmbed (PHP) ──▶ good_event
        /api/method/good_event.embed_api.fragment?kind=event&slug=…&lang=de
   ◀── { html:"<main>…</main>", head_html:"<style>…</style>", meta:{…} }
   Host emits: own <head>+meta + own shell + <main> + CSS  ▶ crawlable
```

1. **good_event content API** (Frappe/Python) — the CMS-agnostic contract. *Built.*
2. **Portable PHP core** (`GoodEventEmbed`) — server-side fetch + render, zero deps. *Built.*
3. **Thin CMS adapters** — TYPO3 `userFunc`, WordPress plugin, plain-PHP example. *Built.*

## 4. Built — good_event side (committed to `main`, CI green)

Repo: `apps/good_event` (github.com/SpendeDirekt/good_event). Relevant commits:

| Commit | What |
|---|---|
| `22904fd` | Public-page SEO metadata (title, meta, Open Graph, `schema.org/Event` JSON-LD) |
| `0b8f23c` | Dynamic sitemap at `/events-sitemap.xml` |
| `7cb0e3d` | Per-catalogue **`seo_public_url`** field + URL resolvers (flexible sitemap/canonicals) |
| `b9f39c6` | **`embed_api.fragment`** content API + metadata-as-data + breadcrumbs + shared list-body partials + canonical double-prefix fix |

**Key files:**
- `good_event/embed_api.py` — the `fragment(kind, slug, lang, preview)` endpoint.
- `good_event/services/seo.py` — URL resolvers (`event_public_url`, `master_public_url`, `list_public_url`, `master_list_public_url`, `_stream_base_urls`), metadata-as-data (`event_detail_meta`, `master_detail_meta`, `listing_meta`), breadcrumbs (`_catalogue_crumb`), sitemap (`build_sitemap_links`).
- `good_event/templates/includes/event_list_body.html`, `event_master_list_body.html` — shared `<main>` partials (live page **and** embed fragment render from these).
- `good_event/www/events_sitemap.py` + `events-sitemap.xml` — the sitemap.
- Doctype field `seo_public_url` on **Good Event List** + **Good Event Master List**; single `seo_public_base_url` on **Good Event Settings**.
- Docs: `apps/good_event/DOCUMENTATION.md` → "SEO metadata", "Server-side embed content API (SEO)".

**Endpoint contract:**
```
GET {baseUrl}/api/method/good_event.embed_api.fragment?kind=<kind>&slug=<slug>&lang=<lang>
kind ∈ event | list | master | master_list      (guest-accessible; no auth)
```
Returns (Frappe wraps in `{"message": …}`):
```jsonc
{ "ok": true, "status": 200, "kind": "event", "slug": "…", "lang": "de",
  "title": "…",
  "head_html": "<style>…theme tokens…</style>",
  "html": "<main class=\"ea-page ea-page--event\">…</main>",   // no chrome
  "meta": { "title","description",
            "canonical": "https://www.kibesuisse.ch/kurse/…",
            "metatags": {"og:title","og:image",…},
            "jsonld": {"@type":"Event",…},
            "breadcrumbs": [{"label":"SWAESS Events","url":"…/kurse"},{"label":"…"}] } }
```
Miss → `{"ok": false, "status": 404}` (HTTP stays 200; branch on `ok`).

## 5. Built — portable PHP package

Location: **`/workspace/development/good-event-embed/`** — standalone git repo (initial commit `b9d8cb2`, branch `main`, **no remote yet**). Ignored by the workspace master repo (`development/*`), so it stays independent. To hand off: add a remote (its own repo, or the kibesuisse TYPO3 repo) and push.

```
src/GoodEventEmbed.php                      # portable core: fetch + renderHead/renderStyles/renderBody/render
adapters/typo3/GoodEventContentElement.php  # userFunc (cached USER); additionalHeaderData → <head> (v8–v13)
adapters/wordpress/good-event-embed.php     # plugin: [good_event kind slug lang] shortcode + wp_head/title hooks
examples/plain-php.php                       # plain-PHP usage
composer.json                                # PSR-4: GoodEvent\Embed\ → src/, …\Typo3\ → adapters/typo3/
README.md                                    # full install/config for all three hosts
```
Requirements: PHP 7.4+, cURL **or** `allow_url_fopen`. No Composer deps. The core
has a built-in server-side cache (`cacheTtl`, default 300s). Host fetch is
**server-to-server**, so no CORS/browser dependency.

## 6. Verified / tested

- All 4 kinds via `embed_api.fragment` **as Guest** (the real public-render identity): body `<main>` + theme `<style>` + full meta.
- Event canonical / Open Graph / JSON-LD / breadcrumbs resolve to the per-catalogue kibesuisse.ch URL **when `seo_public_url` is set** (tested with a temp value, rolled back).
- **Live HTTP wire contract** confirmed unauthenticated: `{"message": {ok, html:<main>, head_html:<style>, meta:{canonical, jsonld@Event, breadcrumbs}}}`; 404 path returns `ok:false`.
- Live `/lists/swaess` + `/course-topics` still render identically through the new shared partials (cache-busted). Canonical de-doubled (`/lists/swaess`, was `/lists/lists/swaess`).
- good_event CI **green** at `b9f39c6`.
- **Not** verified: PHP is not runtime-linted (no PHP in this dev env — reviewed by hand + bracket-balanced) and not yet run against a real TYPO3/WordPress instance.

## 7. TODO to go live (resume here)

1. **good_event deploy config** (Good Event Settings + catalogues):
   - `seo_public_base_url = https://www.kibesuisse.ch`
   - On each **Good Event List** / **Good Event Master List**: set `seo_public_url` (e.g. `https://www.kibesuisse.ch/kurse`, `…/themen`). Events/topics inherit `<that URL>/<slug>`. Flips every canonical/OG/JSON-LD/breadcrumb/sitemap URL to the host.
2. **Give the PHP package a remote** — it's a standalone git repo now (`b9d8cb2`); add a remote (its own GitHub repo, or the kibesuisse TYPO3 repo) and push to hand it off.
3. **TYPO3 wiring on kibesuisse** (site-specific, in their TYPO3 repo — see package README):
   - Route enhancer mapping `/kurse/<slug>` (+ `/themen`, list roots) to a `slug` arg.
   - TypoScript `page.NN = USER` → `GoodEvent\Embed\Typo3\GoodEventContentElement->render` with `baseUrl` + `kind`. Use **cached `USER`** (not `USER_INT`) so SEO head tags reach `<head>`.
   - Clear TYPO3 page cache when an event publishes (later: webhook).
4. **Signup continuity** (so the bounce to good_event's form doesn't look off):
   - Brand good_event's shell to kibesuisse in **Good Event Settings** — see §8.
   - Optionally serve good_event on a host subdomain (`anmeldung.kibesuisse.ch`).
5. **Feed the sitemap** — reference `{baseUrl}/events-sitemap.xml` from the TYPO3/host sitemap index.
6. **Optimization (optional):** the theme `<style>` in `head_html` is ~77 KB (inlined fonts + flatpickr). Fine for SEO; slim to a linkable cached asset for embed performance later.
7. **Phase 2 (only if ever wanted):** embed the registration form too — needs captcha re-key for the host domain, Payrexx return-URLs, cross-origin booking state. Not planned.

## 8. Branding knobs — Good Event Settings (for signup "doesn't look off")

Set these so good_event's hosted signup page looks like kibesuisse.ch:
`client_name`, `logo`, `favicon`, `google_fonts_url`, `primary_color`,
`primary_soft_color`, `secondary_color`, `accent_color`, `text_color`,
`muted_bg_color`, `surface_color`, `border_color`, `heading_font_family`,
`body_font_family`, `header_home_url`, **`header_nav_html`** (Code — paste
kibesuisse's header markup), **`footer_html`** (Text Editor — paste kibesuisse's
footer). The embedded content pages have **no** chrome; only the standalone
signup page uses this shell.

## 9. Notes

- The client-side `public/js/embed.js` still exists (lists/master-lists only) but does not rank; the server-side API supersedes it for SEO.
- CORS: not needed — the host fetches server-side. (`allow_cors:*` is set on the dev site anyway.)
- Dev site: `development16.localhost`; live fetch tested at `http://localhost:8000` (Host: development16.localhost).
